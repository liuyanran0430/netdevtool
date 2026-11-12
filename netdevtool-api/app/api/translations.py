"""翻译任务路由。"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TranslationCreate, TranslationCreated, TranslationOut
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
) -> TranslationCreated:
    try:
        return translation_service.create_translation(db, payload)
    except translation_service.TranslationDispatchError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/{request_id}", response_model=TranslationOut, summary="查询翻译任务状态与结果")
def get_translation(request_id: str, db: Session = Depends(get_db)) -> TranslationOut:
    result = translation_service.get_translation(db, request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="翻译任务不存在")
    return result


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT, summary="取消翻译任务")
def cancel_translation(request_id: str, db: Session = Depends(get_db)) -> Response:
    if not translation_service.cancel_translation(db, request_id):
        raise HTTPException(status_code=404, detail="翻译任务不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
