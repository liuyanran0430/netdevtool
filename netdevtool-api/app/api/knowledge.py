"""知识缺口与补充知识库路由。"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.llm import LLMError, LLMNotConfigured
from app.models import KnowledgeGapKind, KnowledgeGapStatus, User
from app.schemas import (
    CandidateGenerateRequest,
    KnowledgeGapOut,
    SupplementCandidateOut,
    SupplementFileOut,
)
from app.services import knowledge_gap_service, supplement_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


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
