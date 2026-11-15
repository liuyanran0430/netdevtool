"""翻译任务路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    TranslationCreate,
    TranslationCreated,
    TranslationListItem,
    TranslationOut,
    TranslationSourceOut,
)
from app.services import translation_service

router = APIRouter(prefix="/translations", tags=["translations"])


@router.post(
    "",
    response_model=TranslationCreated,
    status_code=status.HTTP_202_ACCEPTED,
    summary="创建异步翻译任务",
)
def create_translation(
    payload: TranslationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TranslationCreated:
    try:
        return translation_service.create_translation(db, payload, user.id)
    except translation_service.TranslationDispatchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("", response_model=list[TranslationListItem], summary="查询当前用户最近的翻译任务")
def list_translations(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TranslationListItem]:
    return translation_service.list_translations(db, user.id, limit)


@router.get("/{request_id}", response_model=TranslationOut, summary="查询翻译任务状态与结果")
def get_translation(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TranslationOut:
    result = translation_service.get_translation(db, request_id, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="翻译任务不存在")
    return result


@router.get("/{request_id}/source", response_model=TranslationSourceOut, summary="查询翻译任务的源配置")
def get_translation_source(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TranslationSourceOut:
    result = translation_service.get_translation_source(db, request_id, user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="翻译任务不存在")
    return result


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT, summary="取消翻译任务")
def cancel_translation(
    request_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    if not translation_service.cancel_translation(db, request_id, user.id):
        raise HTTPException(status_code=404, detail="翻译任务不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
