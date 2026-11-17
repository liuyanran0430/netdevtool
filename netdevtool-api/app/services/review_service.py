"""命令审核：审核条目查询与处置。

审核条目在翻译成功时物化到 review_items（见 review_item_service），处置结果
持久化在 review_decisions 表，按用户与稳定命令标识（item_key）记录。
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models import SupplementCandidateStatus, User
from app.repositories.review_decision_repository import ReviewDecisionRepository
from app.repositories.supplement_candidate_repository import SupplementCandidateRepository
from app.schemas import (
    ReviewDecisionCreate,
    ReviewDecisionOut,
    ReviewDecisionSnapshotOut,
    ReviewHistoryPageOut,
    ReviewItemsPageOut,
)
from app.services import supplement_service
from app.services.review_item_service import (
    build_item_key,
    decision_out,
    list_decision_snapshots,
    list_history_page,
    list_items_page,
)
from app.services.supplement_service import CandidateNotFound, CandidateStateError

logger = logging.getLogger(__name__)


def list_review_items(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 10,
    target_vendor: str | None = None,
    target_model: str | None = None,
    code: str | None = None,
) -> ReviewItemsPageOut:
    """按页读取当前用户的待审核条目、全局统计与筛选项。"""
    return list_items_page(
        db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        target_vendor=target_vendor,
        target_model=target_model,
        code=code,
    )


def list_decisions(db: Session, user_id: int) -> list[ReviewDecisionSnapshotOut]:
    """当前用户全部处置快照，用于审核页生成检查点。"""
    return list_decision_snapshots(db, user_id)


def list_review_history(
    db: Session,
    user_id: int,
    *,
    page: int = 1,
    page_size: int = 10,
    action: str = "all",
    keyword: str | None = None,
) -> ReviewHistoryPageOut:
    """按页读取当前用户的处置记录。"""
    return list_history_page(
        db,
        user_id=user_id,
        page=page,
        page_size=page_size,
        action=action,
        keyword=keyword,
    )


def record_decision(
    db: Session, user: User, payload: ReviewDecisionCreate
) -> ReviewDecisionOut:
    """记录审核处置；带候选时先沉淀补充知识库，失败则整体失败。"""
    item_key = build_item_key(
        source_vendor=payload.source_vendor,
        source_model=payload.source_model,
        target_vendor=payload.target_vendor,
        target_model=payload.target_model,
        source_text=payload.source_text,
    )
    if payload.candidate_id is not None:
        candidate = SupplementCandidateRepository(db).get(payload.candidate_id)
        if candidate is None:
            raise CandidateNotFound(f"候选 {payload.candidate_id} 不存在")
        if candidate.status != SupplementCandidateStatus.accepted:
            supplement_service.accept_candidate(db, candidate.id, user)

    try:
        decision = ReviewDecisionRepository(db).upsert(
            user_id=user.id,
            item_key=item_key,
            action=payload.action,
            decided_text=(payload.decided_text or "").strip() or None,
            candidate_id=payload.candidate_id,
        )
    except Exception:
        # accept_candidate 内部自行提交，处置写入失败时尽力回滚，避免候选悬空
        if payload.candidate_id is not None:
            try:
                supplement_service.revoke_candidate(db, payload.candidate_id, user)
            except Exception:
                logger.exception("处置写入失败后回滚候选失败：candidate_id=%s", payload.candidate_id)
        raise
    return decision_out(decision)


def delete_decision(db: Session, user: User, item_key: str) -> None:
    """撤销处置；候选不再被任何处置引用时回滚补充知识库。"""
    repository = ReviewDecisionRepository(db)
    decision = repository.get_by_key(user.id, item_key)
    if decision is None:
        return
    candidate_id = decision.candidate_id
    if candidate_id is not None and repository.count_by_candidate(candidate_id) <= 1:
        try:
            supplement_service.revoke_candidate(db, candidate_id, user)
        except CandidateStateError:
            logger.info("候选已不处于已采纳状态，跳过回滚：candidate_id=%s", candidate_id)
        except CandidateNotFound:
            logger.warning("候选不存在，跳过回滚：candidate_id=%s", candidate_id)
    repository.delete(decision)
