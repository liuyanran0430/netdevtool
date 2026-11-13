"""契约层：Pydantic 请求校验与统一错误响应。

前端类型由 /openapi.json 生成，此处定义的模型即前后端契约。
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import DeviceType, TranslationTaskStatus


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
