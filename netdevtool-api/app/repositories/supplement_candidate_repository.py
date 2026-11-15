"""补充知识库候选仓储：supplement_candidates 表读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import SupplementCandidate


class SupplementCandidateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, candidate: SupplementCandidate) -> SupplementCandidate:
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get(self, candidate_id: int) -> SupplementCandidate | None:
        return self.db.get(SupplementCandidate, candidate_id)

    def list_by_gap(self, gap_id: int) -> list[SupplementCandidate]:
        stmt = (
            select(SupplementCandidate)
            .where(SupplementCandidate.gap_id == gap_id)
            .order_by(SupplementCandidate.created_at.desc(), SupplementCandidate.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def latest_by_gaps(self, gap_ids: list[int]) -> dict[int, SupplementCandidate]:
        """按缺口取最近一次候选，供审核条目透传 AI 结果。"""
        if not gap_ids:
            return {}
        stmt = (
            select(SupplementCandidate)
            .where(SupplementCandidate.gap_id.in_(gap_ids))
            .order_by(SupplementCandidate.gap_id, SupplementCandidate.id.desc())
        )
        latest: dict[int, SupplementCandidate] = {}
        for candidate in self.db.scalars(stmt):
            latest.setdefault(candidate.gap_id, candidate)
        return latest

    def update(self, candidate: SupplementCandidate) -> SupplementCandidate:
        self.db.commit()
        self.db.refresh(candidate)
        return candidate
