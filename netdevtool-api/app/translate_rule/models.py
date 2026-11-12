"""知识库 YAML 契约模型。

- `entities/{entity_id}.yaml`：规范实体，描述语义与参数。
- `vendors/{vendor}/{device_type}/{entity_id}.yaml`：厂商实现，描述具体命令。
"""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")


def extract_placeholders(template: str) -> set[str]:
    """提取模板中的 `{参数名}`。"""
    return set(PLACEHOLDER_RE.findall(template))


class ParameterType(str, Enum):
    """参数的基础数据类型。"""

    string = "string"
    int = "int"


class ValueFormat(str, Enum):
    """参数的领域取值形态，决定匹配正则与校验方式。"""

    ipv4 = "ipv4"
    ipv4_mask = "ipv4_mask"
    vlan_list = "vlan_list"


class ParameterSpec(BaseModel):
    """实体参数定义。"""

    model_config = ConfigDict(extra="forbid")

    type: ParameterType = ParameterType.string
    format: ValueFormat | None = None
    required: bool = True
    note: str | None = None
    range: tuple[int, int] | None = None
    pattern: str | None = None

    @field_validator("pattern")
    @classmethod
    def _validate_pattern(cls, value: str | None) -> str | None:
        if value:
            re.compile(value)
        return value

    @model_validator(mode="after")
    def _validate_range(self) -> "ParameterSpec":
        if self.range and self.range[0] > self.range[1]:
            raise ValueError("range 下界不能大于上界")
        return self


class EntitySpec(BaseModel):
    """规范实体定义。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    domain: str | None = None
    description: str | None = None
    view_path: list[str] = Field(default_factory=list)
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    semantic_notes: list[str] = Field(default_factory=list)


class AppliesTo(BaseModel):
    """厂商实现适用的设备范围。"""

    model_config = ConfigDict(extra="forbid")

    products: list[str] = Field(default_factory=list)


class Implementation(BaseModel):
    """厂商实现定义。"""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1)
    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    product: str | None = None
    os: str | None = None
    applies_to: AppliesTo | None = None
    supported: bool = True
    confidence: str = "medium"
    pre_commands: list[str] = Field(default_factory=list)
    command: str | None = None
    view: str | None = None
    verified: bool = False
    unsupported_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def _validate_command(self) -> "Implementation":
        if self.supported and not self.command:
            raise ValueError("supported=true 时必须提供 command")
        if not self.supported and not self.unsupported_reason:
            raise ValueError("supported=false 时必须提供 unsupported_reason")
        return self


class VendorProfile(BaseModel):
    """厂商级视图控制配置：退出关键字与收尾行为。"""

    model_config = ConfigDict(extra="forbid")

    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    view_exit: str = Field(default="quit", min_length=1)
    view_return: str = Field(default="return", min_length=1)
    allow_direct_view_switch: bool = False
    auto_close_views: bool = True

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()
