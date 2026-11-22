"""知识缺口与补充知识库路由。"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.llm import LLMError, LLMNotConfigured
from app.models import (
    KnowledgeDocumentFileType,
    KnowledgeDocumentStatus,
    KnowledgeGapKind,
    KnowledgeGapStatus,
    User,
)
from app.schemas import (
    CandidateGenerateRequest,
    KnowledgeBaseConfigUpdate,
    KnowledgeBaseOut,
    KnowledgeDocumentListOut,
    KnowledgeDocumentMetadataBatchUpdate,
    KnowledgeDocumentMetadataUpdate,
    KnowledgeDocumentOut,
    KnowledgeDocumentUploadItem,
    KnowledgeDocumentUploadResult,
    KnowledgeGapOut,
    KnowledgeStatusOut,
    SupplementCandidateOut,
    SupplementFileOut,
)
from app.services import (
    knowledge_base_service,
    knowledge_document_service,
    knowledge_gap_service,
    supplement_service,
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


@router.get("/gaps", response_model=list[KnowledgeGapOut], summary="查询知识缺口")
def list_gaps(
    limit: int = Query(20, ge=1, le=200),
    kind: KnowledgeGapKind | None = None,
    status: KnowledgeGapStatus | None = None,
    vendor: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[KnowledgeGapOut]:
    gaps = knowledge_gap_service.list_gaps(
        db,
        limit=limit,
        kind=kind.value if kind else None,
        status=status.value if status else None,
        vendor=vendor,
    )
    return [KnowledgeGapOut.model_validate(gap) for gap in gaps]


@router.get("/gaps/{gap_id}", response_model=KnowledgeGapOut, summary="查询知识缺口详情")
def get_gap(
    gap_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> KnowledgeGapOut:
    gap = knowledge_gap_service.get_gap(db, gap_id)
    if gap is None:
        raise HTTPException(status_code=404, detail="知识缺口不存在")
    return KnowledgeGapOut.model_validate(gap)


@router.post(
    "/gaps/{gap_id}/candidates",
    response_model=SupplementCandidateOut,
    status_code=status.HTTP_201_CREATED,
    summary="按缺口生成 AI 候选（调用大模型并自动校验）",
)
def generate_candidate(
    gap_id: int,
    payload: CandidateGenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SupplementCandidateOut:
    try:
        candidate = supplement_service.generate_candidate(
            db,
            gap_id,
            target_vendor=payload.target_vendor,
            target_model=payload.target_model,
        )
    except supplement_service.KnowledgeGapNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.TargetDeviceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.SensitiveKnowledgeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return SupplementCandidateOut.model_validate(
        supplement_service.serialize_candidate(candidate)
    )


@router.get(
    "/gaps/{gap_id}/candidates",
    response_model=list[SupplementCandidateOut],
    summary="查询缺口的历史候选",
)
def list_candidates(
    gap_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[SupplementCandidateOut]:
    try:
        candidates = supplement_service.list_candidates(db, gap_id)
    except supplement_service.KnowledgeGapNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        SupplementCandidateOut.model_validate(
            supplement_service.serialize_candidate(candidate)
        )
        for candidate in candidates
    ]


@router.post(
    "/candidates/{candidate_id}/accept",
    response_model=SupplementCandidateOut,
    summary="采纳候选并写入补充知识库",
)
def accept_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplementCandidateOut:
    try:
        candidate = supplement_service.accept_candidate(db, candidate_id, user)
    except supplement_service.CandidateNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.KnowledgeGapNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.CandidateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SupplementCandidateOut.model_validate(
        supplement_service.serialize_candidate(candidate)
    )


@router.post(
    "/candidates/{candidate_id}/revoke",
    response_model=SupplementCandidateOut,
    summary="撤销已采纳的候选（删除补充条目）",
)
def revoke_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplementCandidateOut:
    try:
        candidate = supplement_service.revoke_candidate(db, candidate_id, user)
    except supplement_service.CandidateNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.KnowledgeGapNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.CandidateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SupplementCandidateOut.model_validate(
        supplement_service.serialize_candidate(candidate)
    )


@router.post(
    "/candidates/{candidate_id}/reject",
    response_model=SupplementCandidateOut,
    summary="拒绝候选",
)
def reject_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SupplementCandidateOut:
    try:
        candidate = supplement_service.reject_candidate(db, candidate_id, user)
    except supplement_service.CandidateNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except supplement_service.CandidateStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return SupplementCandidateOut.model_validate(
        supplement_service.serialize_candidate(candidate)
    )


@router.get(
    "/supplements",
    response_model=list[SupplementFileOut],
    summary="查询补充知识库条目",
)
def list_supplements(
    _: User = Depends(get_current_user),
) -> list[SupplementFileOut]:
    return [SupplementFileOut.model_validate(item) for item in supplement_service.list_supplements()]


@router.delete(
    "/supplements/{supplement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除补充条目",
)
def delete_supplement(
    supplement_id: str,
    _: User = Depends(get_current_user),
) -> Response:
    if not supplement_service.delete_supplement(supplement_id):
        raise HTTPException(status_code=404, detail="补充条目不存在")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
