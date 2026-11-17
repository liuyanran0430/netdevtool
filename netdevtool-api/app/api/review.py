"""命令审核路由：分页读取审核条目、导出处置快照与审核处置。"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    ReviewDecisionCreate,
    ReviewDecisionOut,
    ReviewDecisionSnapshotOut,
    ReviewHistoryPageOut,
    ReviewItemsPageOut,
)
from app.services import review_service
from app.services.supplement_service import CandidateNotFound, CandidateStateError

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/items", response_model=ReviewItemsPageOut, summary="分页读取待审核条目")
def list_review_items(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    target_vendor: str | None = Query(None, max_length=64, description="目的厂商"),
    target_model: str | None = Query(None, max_length=128, description="目的型号"),
    code: str | None = Query(None, max_length=64, description="告警类型筛选"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewItemsPageOut:
    return review_service.list_review_items(
        db,
        user.id,
        page=page,
        page_size=page_size,
        target_vendor=target_vendor,
        target_model=target_model,
        code=code,
    )


@router.get(
    "/history",
    response_model=ReviewHistoryPageOut,
    summary="分页读取审核处置记录",
)
def list_review_history(
    page: int = Query(1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    action_filter: Literal["all", "accept", "edit", "skip"] = Query(
        "all", alias="action", description="处置动作筛选"
    ),
    keyword: str | None = Query(None, max_length=255, description="源命令关键词"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewHistoryPageOut:
    return review_service.list_review_history(
        db,
        user.id,
        page=page,
        page_size=page_size,
        action=action_filter,
        keyword=(keyword or "").strip() or None,
    )


@router.get(
    "/decisions",
    response_model=list[ReviewDecisionSnapshotOut],
    summary="导出当前用户全部审核处置快照",
)
def list_decisions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReviewDecisionSnapshotOut]:
    return review_service.list_decisions(db, user.id)


@router.post(
    "/decisions",
    response_model=ReviewDecisionOut,
    summary="记录审核处置（采纳 / 修改后采纳 / 拒绝）",
)
def create_decision(
    payload: ReviewDecisionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewDecisionOut:
    try:
        return review_service.record_decision(db, user, payload)
    except CandidateNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CandidateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete(
    "/decisions/{item_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="撤销审核处置",
)
def delete_decision(
    item_key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    review_service.delete_decision(db, user, item_key)
