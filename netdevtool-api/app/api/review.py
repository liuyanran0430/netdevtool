"""命令审核路由：只提供条目查询，处置动作暂未实现。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ReviewItemsPageOut
from app.services import review_item_service

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/items", response_model=ReviewItemsPageOut, summary="分页读取待审核条目")
def list_review_items(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    target_vendor: str | None = Query(None),
    target_model: str | None = Query(None),
    item_type: str | None = Query(None),
) -> ReviewItemsPageOut:
    return review_item_service.list_items_page(
        db,
        user_id=user.id,
        page=page,
        page_size=page_size,
        target_vendor=target_vendor,
        target_model=target_model,
        item_type=item_type,
    )
