"""ORM 模型：表结构、约束、索引。

新增模型时继承 Base，并在 app/repositories 中提供对应仓储。
"""

from app.database import Base
from app.models.ai_run import AiRun, AiRunKind, AiRunStatus
from app.models.chat import (
    ChatMessage,
    ChatMessageCitation,
    ChatMessageFeedback,
    ChatMessageRole,
    ChatMessageStatus,
    ChatQuestionMode,
    ChatSession,
)
from app.models.device import Device, DeviceType
from app.models.gap import (
    KnowledgeGap,
    KnowledgeGapKind,
    KnowledgeGapStatus,
    SupplementCandidate,
    SupplementCandidateStatus,
)
from app.models.knowledge import (
    KnowledgeBase,
    KnowledgeBaseChunkingMode,
    KnowledgeBaseIndexingMode,
    KnowledgeBaseRetrievalMode,
    KnowledgeBaseType,
    KnowledgeDocument,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStage,
    KnowledgeDocumentStatus,
)
from app.models.review import ReviewDecision, ReviewDecisionAction, ReviewItem
from app.models.translation import TranslationTask, TranslationTaskStatus
from app.models.user import User, UserStatus

__all__ = [
    "AiRun",
    "AiRunKind",
    "AiRunStatus",
    "Base",
    "ChatMessage",
    "ChatMessageCitation",
    "ChatMessageFeedback",
    "ChatMessageRole",
    "ChatMessageStatus",
    "ChatQuestionMode",
    "ChatSession",
    "Device",
    "DeviceType",
    "KnowledgeBase",
    "KnowledgeBaseType",
    "KnowledgeDocument",
    "KnowledgeDocumentFileType",
    "KnowledgeDocumentStatus",
    "KnowledgeDocumentStage",
    "KnowledgeGap",
    "KnowledgeGapKind",
    "KnowledgeGapStatus",
    "KnowledgeBaseChunkingMode",
    "KnowledgeBaseIndexingMode",
    "KnowledgeBaseRetrievalMode",
    "ReviewDecision",
    "ReviewDecisionAction",
    "ReviewItem",
    "SupplementCandidate",
    "SupplementCandidateStatus",
    "TranslationTask",
    "TranslationTaskStatus",
    "User",
    "UserStatus",
]
