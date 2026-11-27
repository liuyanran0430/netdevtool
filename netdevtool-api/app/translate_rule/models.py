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


def split_optional_chunks(template: str) -> list[tuple[str, bool]]:
    """按 `[ ... ]` 把模板拆成必选/可选片段，返回 `(片段, 是否可选)`。

    可选片段表示源配置中可省略的命令部分，如 `ospf {process_id} [router-id {router_id}]`。
    """
    chunks: list[tuple[str, bool]] = []
    buffer: list[str] = []
    optional = False
    for token in template.split():
        starts = token.startswith("[")
        ends = token.endswith("]")
        if starts:
            if optional:
                raise ValueError(f"可选片段不支持嵌套：{template}")
            if buffer:
                chunks.append((" ".join(buffer), False))
                buffer = []
            optional = True
        elif ends and not optional:
            raise ValueError(f"可选片段未开始就结束：{template}")
        token = token.strip("[]")
        if token:
            buffer.append(token)
        if ends:
            if buffer:
                chunks.append((" ".join(buffer), optional))
                buffer = []
            optional = False
    if optional:
        raise ValueError(f"可选片段未闭合：{template}")
    if buffer:
        chunks.append((" ".join(buffer), False))
    return chunks


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
    # 缺省值模板：参数未提供时用其它参数推导，如 bd_id: "{vni}"
    default: str | None = None
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
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    # 重复参数组：组名 -> 每行包含的字段，如 peers: [vni, peer_ip]
    collections: dict[str, list[str]] = Field(default_factory=dict)
    semantic_notes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_defaults(self) -> "EntitySpec":
        for name, parameter in self.parameters.items():
            if not parameter.default:
                continue
            refs = extract_placeholders(parameter.default)
            unknown = refs - set(self.parameters)
            if unknown:
                raise ValueError(
                    f"{name}.default 引用了未定义参数 {sorted(unknown)}"
                )
            if name in refs:
                raise ValueError(f"{name}.default 不能引用自身")
        for collection, fields in self.collections.items():
            if not collection.strip() or not fields:
                raise ValueError("collections 的组名和字段列表不能为空")
            unknown = set(fields) - set(self.parameters)
            if unknown:
                raise ValueError(
                    f"collections.{collection} 引用了未定义参数 {sorted(unknown)}"
                )
            if len(set(fields)) != len(fields):
                raise ValueError(f"collections.{collection} 存在重复字段")
        return self


class AppliesTo(BaseModel):
    """厂商实现适用的设备范围。"""

    model_config = ConfigDict(extra="forbid")

    products: list[str] = Field(default_factory=list)


class PreCommand(BaseModel):
    """视图相关的前置命令。

    - 字符串写法：在实体自身视图内输出（默认行为）。
    - 指定 `view` 时：先进入该视图输出命令，再退回根视图继续渲染实体。
    """

    model_config = ConfigDict(extra="forbid")

    command: str = Field(min_length=1)
    view: str | None = None


class LineSpec(BaseModel):
    """段内一行命令；text 同时用于源匹配与目标生成。"""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    each: str | None = None
    aliases: list[str] = Field(default_factory=list)
    negative_text: str | None = None


class SegmentSpec(BaseModel):
    """一个完整配置段，可包含多行和重复项。"""

    model_config = ConfigDict(extra="forbid")

    key: list[str] = Field(default_factory=list)
    each: str | None = None
    path: list[str] = Field(default_factory=list)
    lines: list[LineSpec] = Field(default_factory=list)
    # 段头本身即为配置对象：无成员命中时也按段头参数生成实体
    header_entity: bool = False


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
    pre_commands: list[str | PreCommand] = Field(default_factory=list)
    segments: list[SegmentSpec] = Field(default_factory=list)
    param_formats: dict[str, str] = Field(default_factory=dict)
    # 参数取值映射：实体参数值 → 本厂商取值（如 stp → sstp）
    param_values: dict[str, dict[str, str]] = Field(default_factory=dict)
    verified: bool = False
    unsupported_reason: str | None = None
    warnings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    # 来源层：core=人工维护的核心层，supplement=AI 兜底沉淀的补充层
    origin: str = "core"

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("origin")
    @classmethod
    def _check_origin(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"core", "supplement"}:
            raise ValueError("origin 仅支持 core / supplement")
        return normalized

    @field_validator("param_formats")
    @classmethod
    def _check_param_formats(cls, value: dict[str, str]) -> dict[str, str]:
        allowed = {"to", "hyphen"}
        for name, style in value.items():
            if style not in allowed:
                raise ValueError(f"param_formats.{name} 仅支持 {sorted(allowed)}")
        return value

    @field_validator("param_values")
    @classmethod
    def _check_param_values(
        cls, value: dict[str, dict[str, str]]
    ) -> dict[str, dict[str, str]]:
        for name, mapping in value.items():
            if not name.strip():
                raise ValueError("param_values 的参数名不能为空")
            for source, target in mapping.items():
                if not str(source).strip() or not str(target).strip():
                    raise ValueError(f"param_values.{name} 的取值不能为空")
        return value

    @model_validator(mode="after")
    def _validate_command(self) -> "Implementation":
        if self.supported and not self.segments:
            raise ValueError("supported=true 时必须提供 segments")
        if not self.supported and not self.unsupported_reason:
            raise ValueError("supported=false 时必须提供 unsupported_reason")
        return self


class VendorProfile(BaseModel):
    """厂商级视图控制配置：退出关键字、收尾行为与显示命令关键字。"""

    model_config = ConfigDict(extra="forbid")

    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    # 根视图（全局配置视图），如 system-view / configure terminal
    root_view: str = Field(default="system-view", min_length=1)
    view_exit: str = Field(default="quit", min_length=1)
    view_return: str = Field(default="return", min_length=1)
    negation_prefix: str = Field(default="undo", min_length=1)
    # 显示/查看命令关键字：源侧用于识别，目标侧用于生成
    display_prefix: str = Field(default="display", min_length=1)
    allow_direct_view_switch: bool = False
    auto_close_views: bool = True

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("display_prefix")
    @classmethod
    def _normalize_display_prefix(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("display_prefix 不能为空")
        return normalized

    @field_validator("root_view")
    @classmethod
    def _normalize_root_view(cls, value: str) -> str:
        normalized = " ".join(value.strip().lower().split())
        if not normalized:
            raise ValueError("root_view 不能为空")
        return normalized


class InterfaceNaming(BaseModel):
    """厂商接口命名规则：规范类型 → 含 `{number}` 的接口名模板。"""

    model_config = ConfigDict(extra="forbid")

    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    interfaces: dict[str, str] = Field(default_factory=dict)

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("interfaces")
    @classmethod
    def _check_placeholders(cls, value: dict[str, str]) -> dict[str, str]:
        for type_key, template in value.items():
            if extract_placeholders(template) != {"number"}:
                raise ValueError(f"{type_key}: 接口模板必须且只能包含 {{number}}")
        return value


class SupplementSource(BaseModel):
    """补充条目：源侧命令定义。"""

    model_config = ConfigDict(extra="forbid")

    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    product: str | None = None
    os: str | None = None
    view_path: list[str] = Field(default_factory=list)
    command: str = Field(min_length=1)
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()


class SupplementTarget(BaseModel):
    """补充条目：目标侧命令定义。"""

    model_config = ConfigDict(extra="forbid")

    vendor: str = Field(min_length=1)
    device_type: str = Field(min_length=1)
    product: str | None = None
    os: str | None = None
    view_path: list[str] = Field(default_factory=list)
    command: str = Field(min_length=1)
    pre_commands: list[str] = Field(default_factory=list)
    negative_command: str | None = None

    @field_validator("vendor", "device_type")
    @classmethod
    def _normalize_lower(cls, value: str) -> str:
        return value.strip().lower()


class SupplementCase(BaseModel):
    """补充条目的真实用例，供人工核对。"""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    target: str = Field(min_length=1)


class SupplementEntry(BaseModel):
    """`supplements/{source_vendor}/{device_type}/{slug}.yaml` 的契约。"""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    source: SupplementSource
    target: SupplementTarget
    origin: str = "llm"
    verified: bool = False
    accepted_by: str | None = None
    accepted_at: str | None = None
    uses: int = 0
    sources: list[str] = Field(default_factory=list)
    cases: list[SupplementCase] = Field(default_factory=list)
