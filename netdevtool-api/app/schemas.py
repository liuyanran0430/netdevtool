"""契约层：Pydantic 请求校验与统一错误响应。

前端类型由 /openapi.json 生成，此处定义的模型即前后端契约。
"""

from typing import Any
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import (
    DeviceType,
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


class TranslationResultLine(APIModel):
    no: int
    text: str
    tone: str
    source_no: int | None = None
    entity_id: str | None = None


class TranslationWarning(APIModel):
    """行级告警，`no` 为源配置行号。"""

    no: int
    message: str
    code: str = "unknown"
    severity: str = "warn"
    # unsupported_entity 的细分原因：missing_impl / explicit_unsupported / entity_missing
    reason: str | None = None


class TranslationEntityInfo(APIModel):
    """结果中引用的规范实体及其说明。"""

    id: str
    description: str | None = None


class TranslationResultSummary(APIModel):
    total: int
    duration_ms: int


class TranslationResult(APIModel):
    lines: list[TranslationResultLine]
    warnings: list[TranslationWarning] = []
    entities: list[TranslationEntityInfo] = []
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
    llm_model: str
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
    decision: ReviewDecisionOut | None = None
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
    llm_model: str
    prompt_version: str
    response: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
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
