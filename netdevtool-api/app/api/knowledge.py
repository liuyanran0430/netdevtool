"""知识库路由：知识库配置与文档管理。"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import (
    KnowledgeDocumentFileType,
    KnowledgeDocumentStatus,
    User,
)
from app.schemas import (
    KnowledgeBaseConfigUpdate,
    KnowledgeBaseOut,
    KnowledgeDocumentListOut,
    KnowledgeDocumentMetadataBatchUpdate,
    KnowledgeDocumentMetadataUpdate,
    KnowledgeDocumentOut,
    KnowledgeDocumentUploadItem,
    KnowledgeDocumentUploadResult,
    KnowledgeStatusOut,
)
from app.services import (
    knowledge_base_service,
    knowledge_document_service,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get(
    "/status",
    response_model=KnowledgeStatusOut,
    summary="查询知识库连接状态",
)
def get_knowledge_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeStatusOut:
    return KnowledgeStatusOut(**knowledge_base_service.get_connection_status(db))


@router.get("/bases", response_model=list[KnowledgeBaseOut], summary="查询知识库列表")
def list_knowledge_bases(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[KnowledgeBaseOut]:
    bases = knowledge_base_service.list_knowledge_bases(db)
    return [KnowledgeBaseOut.model_validate(base) for base in bases]


@router.put(
    "/bases/{base_id}/config",
    response_model=KnowledgeBaseOut,
    summary="更新知识库向量与检索配置",
)
def update_knowledge_base_config(
    base_id: int,
    payload: KnowledgeBaseConfigUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeBaseOut:
    base = knowledge_base_service.update_knowledge_base_config(db, base_id, payload)
    if base is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return KnowledgeBaseOut.model_validate(base)


@router.post(
    "/bases/{base_id}/documents",
    response_model=KnowledgeDocumentUploadResult,
    status_code=status.HTTP_201_CREATED,
    summary="上传知识库文档（逐文件返回结果）",
)
async def upload_knowledge_documents(
    base_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeDocumentUploadResult:
    payload = [
        (upload.filename or "unnamed", await upload.read()) for upload in files
    ]
    try:
        results = knowledge_document_service.upload_documents(db, base_id, payload)
    except knowledge_document_service.KnowledgeBaseNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except knowledge_document_service.UploadLimitError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeDocumentUploadResult(
        items=[
            KnowledgeDocumentUploadItem(
                file_name=str(item["file_name"]),
                result=item["result"],  # type: ignore[arg-type]
                doc=(
                    KnowledgeDocumentOut.model_validate(item["doc"])
                    if item["doc"] is not None
                    else None
                ),
                error=item["error"],  # type: ignore[arg-type]
            )
            for item in results
        ]
    )


@router.get(
    "/bases/{base_id}/documents",
    response_model=KnowledgeDocumentListOut,
    summary="查询知识库文档列表",
)
def list_knowledge_documents(
    base_id: int,
    status_filter: KnowledgeDocumentStatus | None = Query(default=None, alias="status"),
    file_type: KnowledgeDocumentFileType | None = None,
    keyword: str | None = Query(default=None, max_length=128),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeDocumentListOut:
    try:
        items, total, indexed_count, processing_count = (
            knowledge_document_service.list_documents(
                db,
                base_id,
                status=status_filter,
                file_type=file_type,
                keyword=keyword,
                page=page,
                page_size=page_size,
            )
        )
    except knowledge_document_service.KnowledgeBaseNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return KnowledgeDocumentListOut(
        items=[KnowledgeDocumentOut.model_validate(item) for item in items],
        total=total,
        indexed_count=indexed_count,
        processing_count=processing_count,
    )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除知识库文档及其向量",
)
def delete_knowledge_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Response:
    try:
        knowledge_document_service.delete_document(db, doc_id)
    except knowledge_document_service.KnowledgeDocumentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except knowledge_document_service.DocumentBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/documents/{doc_id}/retry",
    response_model=KnowledgeDocumentOut,
    summary="重试文档索引",
)
def retry_knowledge_document(
    doc_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeDocumentOut:
    try:
        document = knowledge_document_service.retry_document(db, doc_id)
    except knowledge_document_service.KnowledgeDocumentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except knowledge_document_service.DocumentBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return KnowledgeDocumentOut.model_validate(document)


@router.patch(
    "/documents/metadata",
    response_model=list[KnowledgeDocumentOut],
    summary="批量更新文档元数据",
)
def update_knowledge_documents_metadata(
    payload: KnowledgeDocumentMetadataBatchUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[KnowledgeDocumentOut]:
    try:
        documents = knowledge_document_service.update_documents_metadata(
            db,
            payload.ids,
            payload.metadata,
        )
    except knowledge_document_service.KnowledgeDocumentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [KnowledgeDocumentOut.model_validate(document) for document in documents]


@router.patch(
    "/documents/{doc_id}/metadata",
    response_model=KnowledgeDocumentOut,
    summary="更新文档元数据",
)
def update_knowledge_document_metadata(
    doc_id: int,
    payload: KnowledgeDocumentMetadataUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeDocumentOut:
    try:
        document = knowledge_document_service.update_document_metadata(
            db,
            doc_id,
            payload.metadata,
        )
    except knowledge_document_service.KnowledgeDocumentNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return KnowledgeDocumentOut.model_validate(document)
