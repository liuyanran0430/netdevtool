"""契约层：Pydantic 请求校验与统一错误响应。

前端类型由 /openapi.json 生成，此处定义的模型即前后端契约。
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import (
    ChatMessageRole,
    ChatMessageStatus,
    ChatQuestionMode,
    DeviceType,
    KnowledgeBaseChunkingMode,
    KnowledgeBaseIndexingMode,
    KnowledgeBaseRetrievalMode,
    KnowledgeDocumentFileType,
    KnowledgeDocumentStage,
    KnowledgeDocumentStatus,
    KnowledgeGapKind,
    KnowledgeGapStatus,
    ReviewDecisionAction,
    SupplementCandidateStatus,
    TranslationTaskStatus,
    UserStatus,
)


class APIModel(BaseModel):
    """接口模型基类，支持从 ORM 实例转换。"""

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """统一错误响应体。"""

    code: int
    message: str
    detail: Any | None = None


class DeviceOut(APIModel):
    """设备出参。"""

    id: int
    vendor: str
    vendor_en: str | None = None
    model: str
    device_type: DeviceType


class DeviceManualOut(BaseModel):
    """外部手册链接；本地文件由接口直接返回文件流。"""

    kind: str
    url: str


class KnowledgeBaseOut(APIModel):
    """知识库出参，包含向量与检索配置。"""

    id: int
    name: str
    vector_store_name: str
    chunking_mode: KnowledgeBaseChunkingMode
    general_delimiter: str | None = None
    general_max_length: int | None = None
    general_overlap: int | None = None
    parent_max_length: int | None = None
    child_delimiter: str | None = None
    child_max_length: int | None = None
    heading_split_levels: str = "1,2"
    indexing_mode: KnowledgeBaseIndexingMode
    retrieval_mode: KnowledgeBaseRetrievalMode
    hybrid_semantic_weight: int
    hybrid_top_k: int
    hybrid_score_threshold: float
    created_at: datetime
    updated_at: datetime


class KnowledgeStatusOut(BaseModel):
    """知识库连接状态：数据库与 Qdrant 可用性。"""

    connected: bool
    database: bool
    qdrant: bool
    knowledge_bases: int
    detail: str | None = None


class KnowledgeBaseConfigUpdate(BaseModel):
    """知识库向量与检索配置更新入参。"""

    chunking_mode: KnowledgeBaseChunkingMode
    general_delimiter: str = Field(default="", max_length=32)
    general_max_length: int | None = Field(default=None, ge=1, le=5000)
    general_overlap: int | None = Field(default=None, ge=0, le=5000)
    parent_max_length: int | None = Field(default=None, ge=1, le=5000)
    child_delimiter: str = Field(default="", max_length=32)
    child_max_length: int | None = Field(default=None, ge=1, le=5000)
    heading_split_levels: str = Field(
        default="1,2",
        max_length=16,
        pattern=r"^$|^[1-6](,[1-6])*$",
        description="父块标题硬边界级别，逗号分隔；空表示不按标题切",
    )
    indexing_mode: KnowledgeBaseIndexingMode
    retrieval_mode: KnowledgeBaseRetrievalMode
    hybrid_semantic_weight: int = Field(ge=0, le=100)
    hybrid_top_k: int = Field(ge=1, le=50)
    hybrid_score_threshold: float = Field(ge=0, le=1)


class KnowledgeDocumentOut(APIModel):
    """知识库文档出参，包含状态、阶段与进度。"""

    id: int
    kb_id: int
    file_name: str
    file_type: KnowledgeDocumentFileType
    file_size: int
    file_hash: str
    status: KnowledgeDocumentStatus
    stage: KnowledgeDocumentStage | None = None
    progress: int
    total_chunks: int | None = None
    processed_chunks: int
    chunk_count: int | None = None
    metadata_json: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentUploadItem(BaseModel):
    """单个文件的上传结果。"""

    file_name: str
    result: Literal["created", "duplicated", "failed"]
    doc: KnowledgeDocumentOut | None = None
    error: str | None = None


class KnowledgeDocumentUploadResult(BaseModel):
    """批量上传结果。"""

    items: list[KnowledgeDocumentUploadItem]


class KnowledgeDocumentListOut(BaseModel):
    """知识库文档列表与统计信息。"""

    items: list[KnowledgeDocumentOut]
    total: int
    indexed_count: int
    processing_count: int


def _validate_metadata_pairs(value: dict[str, str]) -> dict[str, str]:
    if len(value) > 50:
        raise ValueError("元数据项不能超过 50 个")
    for key in value:
        if not key.strip():
            raise ValueError("元数据键不能为空")
        if len(key) > 64:
            raise ValueError("元数据键长度不能超过 64 个字符")
    return value


class KnowledgeDocumentMetadataUpdate(BaseModel):
    """更新单篇文档的元数据键值对。"""

    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return _validate_metadata_pairs(value)


class KnowledgeDocumentMetadataBatchUpdate(BaseModel):
    """批量更新多篇文档的元数据键值对。"""

    ids: list[int] = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, str]) -> dict[str, str]:
        return _validate_metadata_pairs(value)


class TranslationCreate(BaseModel):
    """创建翻译任务入参。"""

    source_text: str = Field(min_length=1, max_length=2 * 1024 * 1024)
    source_vendor: str = Field(min_length=1, max_length=64)
    source_model: str = Field(min_length=1, max_length=128)
    target_vendor: str = Field(min_length=1, max_length=64)
    target_model: str = Field(min_length=1, max_length=128)

    @field_validator("source_text")
    @classmethod
    def validate_source_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("源配置不能为空")
        return value


class TranslationCreated(APIModel):
    """创建翻译任务出参。"""

    request_id: str
    status: TranslationTaskStatus


class TranslationResultLines(APIModel):
    """渲染输出的一行纯文本，顺序即目标配置顺序。"""

    text: str
    tone: str


class TranslationWarning(APIModel):
    """实体级告警，直接关联到某个 entity，不再需要逐行匹配。"""

    entity_id: str | None = None
    message: str
    code: str = "unknown"
    severity: str = "warn"
    # 该告警覆盖的源配置行号（冗余，供前端定位）
    no: list[int] = []


class TranslationEntityInfo(APIModel):
    """实体分组的联动元数据。source_nos → 源面板高亮，target_line_indices → 目标面板高亮。"""

    id: str
    source_nos: list[int] = []
    # 实体自身命令行号（不含视图头行），前端据此区分视图行与命令行
    command_nos: list[int] = []
    target_line_indices: list[int] = []
    description: str | None = None


class TranslationResultSummary(APIModel):
    total: int
    duration_ms: int


class TranslationResult(APIModel):
    lines: list[TranslationResultLines]
    # 与 lines 平行的源行号映射：无实体行（未识别命令、显示命令）记录其源行号，其余为 None
    line_source_nos: list[int | None] = []
    entities: list[TranslationEntityInfo] = []
    warnings: list[TranslationWarning] = []
    summary: TranslationResultSummary


class TranslationOut(APIModel):
    """翻译任务查询出参，仅成功时携带结果。"""

    request_id: str
    status: TranslationTaskStatus
    result: TranslationResult | None = None
    error: str | None = None


class TranslationListItem(APIModel):
    """翻译历史列表项，不含源配置与结果等大字段。"""

    request_id: str
    status: TranslationTaskStatus
    source_vendor: str
    source_model: str
    target_vendor: str
    target_model: str
    created_at: datetime
    finished_at: datetime | None = None


class TranslationSourceOut(APIModel):
    """翻译任务的源配置，用于历史记录恢复。"""

    request_id: str
    source_text: str
    source_vendor: str
    source_model: str
    target_vendor: str
    target_model: str
    status: TranslationTaskStatus


class ReviewCandidateOut(APIModel):
    """审核条目关联的最近一次 AI 候选。"""

    id: int
    status: SupplementCandidateStatus
    command: str | None = None
    views: list[str] = Field(default_factory=list)
    reasoning: str | None = None
    passed: bool = False
    created_at: datetime


class ReviewDecisionOut(APIModel):
    """审核处置结果。"""

    item_key: str
    action: ReviewDecisionAction
    decided_text: str | None = None
    candidate_id: int | None = None


class ReviewDecisionCreate(BaseModel):
    """提交审核处置：由后端按设备与源命令重新计算 item_key。"""

    source_vendor: str
    source_model: str
    target_vendor: str
    target_model: str
    source_text: str
    action: ReviewDecisionAction
    decided_text: str | None = None
    candidate_id: int | None = None

    @model_validator(mode="after")
    def _check_action(self) -> "ReviewDecisionCreate":
        if self.action == ReviewDecisionAction.edit and not (self.decided_text or "").strip():
            raise ValueError("修改后采纳必须提供命令文本")
        if self.candidate_id is not None and self.action != ReviewDecisionAction.accept:
            raise ValueError("仅采纳动作可以关联 AI 候选")
        return self


class ReviewItemOut(APIModel):
    """待审条目，`line_index` 为结果行序号（从 1 开始）。"""

    request_id: str
    line_index: int
    item_key: str
    source_no: int | None = None
    codes: list[str]
    severity: str
    source_vendor: str
    source_model: str
    target_vendor: str
    target_model: str
    gap_id: int | None = None
    candidate: ReviewCandidateOut | None = None
    view: str
    source_text: str
    target_text: str
    message: str
    created_at: datetime


class ReviewStatsOut(APIModel):
    """审核条目全局统计（不受筛选影响）。"""

    pending: int
    accepted: int
    edited: int
    skipped: int


class ReviewTargetOptionOut(APIModel):
    """目的型号筛选项。"""

    vendor: str
    model: str


class ReviewItemsPageOut(APIModel):
    """审核条目分页结果，附带全局统计与筛选项。"""

    items: list[ReviewItemOut]
    total: int
    page: int
    page_size: int
    stats: ReviewStatsOut
    target_options: list[ReviewTargetOptionOut]
    code_options: list[str]


class ReviewDecisionSnapshotOut(APIModel):
    """处置快照：审核页生成检查点时按来源行回填。"""

    request_id: str
    line_index: int
    action: ReviewDecisionAction
    decided_text: str | None = None
    original_tone: str


class ReviewHistoryItemOut(APIModel):
    """审核记录条目：一条处置及其关联命令的展示信息。"""

    item_key: str
    action: ReviewDecisionAction
    decided_text: str | None = None
    request_id: str
    source_vendor: str
    source_model: str
    target_vendor: str
    target_model: str
    view: str
    source_text: str
    target_text: str
    codes: list[str]
    severity: str
    candidate: ReviewCandidateOut | None = None
    created_at: datetime
    updated_at: datetime


class ReviewHistoryPageOut(APIModel):
    """审核记录分页结果。"""

    items: list[ReviewHistoryItemOut]
    total: int
    page: int
    page_size: int


class UserOut(APIModel):
    """用户出参，永不包含密码哈希。"""

    id: int
    username: str
    name: str
    status: UserStatus


class LoginRequest(BaseModel):
    """登录入参。"""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(APIModel):
    """登录出参：令牌 + 当前用户。"""

    token: str
    user: UserOut


class KnowledgeGapOut(APIModel):
    """知识缺口出参。"""

    id: int
    vendor: str
    device_type: DeviceType
    product: str
    os: str | None = None
    target_vendor: str = ""
    target_device_type: str = ""
    view: str | None = None
    command_template: str
    raw_sample: str | None = None
    occurrences: int
    kind: KnowledgeGapKind
    status: KnowledgeGapStatus
    request_ids: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class CandidateGenerateRequest(BaseModel):
    """生成候选入参：需明确目标设备，用于确定目标厂商命令与视图。"""

    target_vendor: str = Field(min_length=1, max_length=64)
    target_model: str = Field(min_length=1, max_length=128)


class SupplementCandidateOut(BaseModel):
    """候选出参：原始模型返回与自动校验结果均以结构化 JSON 返回。"""

    id: int
    gap_id: int
    status: SupplementCandidateStatus
    response: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    rag: dict[str, Any] | None = None
    created_at: datetime
    reviewed_at: datetime | None = None


class SupplementFileOut(BaseModel):
    """补充知识库条目出参（文件形态）。"""

    id: str
    path: str
    source_vendor: str | None = None
    source_device_type: str | None = None
    source_command: str | None = None
    target_vendor: str | None = None
    target_device_type: str | None = None
    target_command: str | None = None
    accepted_by: str | None = None
    accepted_at: str | None = None
    verified: bool = False
    uses: int = 0


class ChatCitationOut(APIModel):
    """回答引用来源，用于前端展示「参考来源」并支持查看命中片段。"""

    doc_id: int | None = None
    file_name: str | None = None
    score: float | None = None
    snippet: str | None = None


class ChatMessageOut(APIModel):
    """会话消息出参。"""

    id: int
    role: ChatMessageRole
    content: str
    status: ChatMessageStatus
    mode: ChatQuestionMode
    evidenced: bool = Field(
        default=False, description="是否基于知识库检索证据生成（引用数 > 0）"
    )
    citations: list[ChatCitationOut] = Field(
        default_factory=list, description="回答引用的知识库来源，无引用时为空"
    )
    feedback: int | None = Field(
        default=None, description="当前用户对该回答的反馈：1=赞, -1=踩, 空=未反馈"
    )
    created_at: datetime


class ChatSessionOut(APIModel):
    """会话列表出参。"""

    id: int
    title: str
    vendor: str | None = None
    message_count: int
    last_message_at: datetime | None = None
    created_at: datetime


class ChatSessionDetailOut(ChatSessionOut):
    """会话详情出参：包含按时间排列的全部消息。"""

    messages: list[ChatMessageOut] = Field(default_factory=list)


class ChatMessageCreate(BaseModel):
    """发送消息入参；`session_id` 为空时自动创建新会话。"""

    session_id: int | None = Field(default=None, ge=1)
    content: str = Field(min_length=1, max_length=8000)
    mode: ChatQuestionMode = ChatQuestionMode.unknown
    vendor: str | None = Field(default=None, max_length=64)


class ChatProgressOut(BaseModel):
    """问答处理阶段：intent / retrieval / generation；None 表示已结束或未知。"""

    stage: str | None = None


class ChatSessionRename(BaseModel):
    """重命名会话入参。"""

    title: str = Field(min_length=1, max_length=128)


class ChatFeedbackIn(BaseModel):
    """回答反馈入参：rating=-1 时必须给出原因，0 表示取消反馈。"""

    rating: int = Field(..., ge=-1, le=1, description="1=赞, -1=踩, 0=取消")
    reason: str | None = Field(default=None, max_length=255, description="点踩原因")

    @model_validator(mode="after")
    def _normalize(self) -> "ChatFeedbackIn":
        if self.rating == -1:
            reason = " ".join((self.reason or "").split())
            if not reason:
                raise ValueError("点踩需要填写原因")
            self.reason = reason[:255]
        elif self.rating == 1:
            self.reason = None
        return self


class ChatFeedbackOut(APIModel):
    """回答反馈出参：rating=0 表示已取消。"""

    message_id: int
    rating: int
    reason: str | None = None
