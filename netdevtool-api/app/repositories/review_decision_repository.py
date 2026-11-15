"""审核处置仓储：review_decisions 表读写唯一入口。"""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ReviewDecision, ReviewDecisionAction


class ReviewDecisionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_key(self, user_id: int, item_key: str) -> ReviewDecision | None:
        stmt = select(ReviewDecision).where(
            ReviewDecision.user_id == user_id,
            ReviewDecision.item_key == item_key,
        )
        return self.db.scalars(stmt).first()

    def upsert(
        self,
        *,
        user_id: int,
        item_key: str,
        action: ReviewDecisionAction,
        decided_text: str | None,
        candidate_id: int | None,
    ) -> ReviewDecision:
        decision = self.get_by_key(user_id, item_key)
        if decision is None:
            decision = ReviewDecision(
                user_id=user_id,
                item_key=item_key,
                action=action,
                decided_text=decided_text,
                candidate_id=candidate_id,
            )
            self.db.add(decision)
            try:
                self.db.commit()
            except IntegrityError:
                # 并发写入时由唯一键兜底，退回更新已有记录
                self.db.rollback()
                decision = self.get_by_key(user_id, item_key)
                if decision is None:
                    raise
                decision.action = action
                decision.decided_text = decided_text
                decision.candidate_id = candidate_id
                self.db.commit()
        else:
            decision.action = action
            decision.decided_text = decided_text
            decision.candidate_id = candidate_id
            self.db.commit()
        self.db.refresh(decision)
        return decision

    def delete(self, decision: ReviewDecision) -> None:
        self.db.delete(decision)
        self.db.commit()

    def count_by_candidate(self, candidate_id: int) -> int:
        """统计候选被引用的处置记录数，跨用户计算避免误删他人仍在用的规则。"""
        stmt = select(func.count()).select_from(ReviewDecision).where(
            ReviewDecision.candidate_id == candidate_id
        )
        return int(self.db.scalar(stmt) or 0)
