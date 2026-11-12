"""命令渲染：用目标厂商实现替换参数，并按视图层级输出。"""

import re
from dataclasses import dataclass, field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    ParameterType,
    ValueFormat,
)
from app.translate_rule.parser import IPV4_PATTERN, VLAN_LIST_PATTERN, ParsedLine
from app.translate_rule.registry import KnowledgeRegistry

TONE_SUCCESS = "success"
TONE_WARN = "warn"
TONE_MUTED = "muted"

_IPV4_FULL = re.compile(rf"^{IPV4_PATTERN}$")


@dataclass(frozen=True)
class RenderedLine:
    """输出行，`no` 对齐源配置行号。"""

    no: int
    text: str
    tone: str


@dataclass(frozen=True)
class RenderWarning:
    """行级告警，供前端定位。"""

    no: int
    message: str


@dataclass
class TranslationOutput:
    """一次渲染的完整产物。"""

    lines: list[RenderedLine] = field(default_factory=list)
    warnings: list[RenderWarning] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    meta: dict[str, object] = field(default_factory=dict)


class Renderer:
    """把解析结果渲染为目标厂商命令。"""

    def __init__(
        self,
        registry: KnowledgeRegistry,
        target_vendor: str,
        target_device_type: str,
        *,
        source_vendor: str | None = None,
        source_device_type: str | None = None,
    ) -> None:
        self._registry = registry
        self._target_vendor = target_vendor.strip().lower()
        self._target_device_type = target_device_type.strip().lower()
        self._source_vendor = source_vendor.strip().lower() if source_vendor else None
        self._source_device_type = source_device_type.strip().lower() if source_device_type else None
        self._profile = registry.get_profile(self._target_vendor, self._target_device_type)

    def render(self, parsed_lines: list[ParsedLine], duration_ms: int = 0) -> TranslationOutput:
        output = TranslationOutput()
        output.meta = {
            "source": {"vendor": self._source_vendor, "device_type": self._source_device_type},
            "target": {"vendor": self._target_vendor, "device_type": self._target_device_type},
        }
        translated = 0
        unsupported = 0
        used: list[str] = []
        current_view_path: list[str] = []

        for item in parsed_lines:
            if item.kind in {"view", "pre"}:
                # 视图指令与 pre 行不直接输出，由渲染器按目标视图差异补齐
                continue
            if item.kind in {"blank", "comment", "other"}:
                output.lines.append(RenderedLine(item.no, item.text, TONE_MUTED))
                continue

            entity = item.entity
            if entity is None:
                output.lines.append(RenderedLine(item.no, item.text, TONE_MUTED))
                continue

            spec = self._registry.get_entity(entity.entity_id)
            implementation = self._registry.resolve(
                self._target_vendor, self._target_device_type, entity.entity_id
            )
            if spec is None or implementation is None or not implementation.supported:
                output.lines.append(
                    RenderedLine(item.no, f"# 目标设备不支持: {entity.entity_id}", TONE_WARN)
                )
                output.warnings.append(RenderWarning(item.no, "目标设备不支持该实体"))
                unsupported += 1
                continue

            errors = _validate_parameters(spec, entity.params)
            if errors:
                message = "；".join(errors)
                output.lines.append(
                    RenderedLine(item.no, f"# 参数校验失败: {entity.entity_id}（{message}）", TONE_WARN)
                )
                output.warnings.append(RenderWarning(item.no, message))
                unsupported += 1
                continue

            view_path = [_render_template(template, entity.params) for template in spec.view_path]
            if not view_path and implementation.view:
                view_path = [implementation.view]

            common = _common_prefix(current_view_path, view_path)
            if not self._profile.allow_direct_view_switch:
                for level in range(len(current_view_path), common, -1):
                    output.lines.append(
                        RenderedLine(
                            item.no,
                            "  " * (level - 1) + self._profile.view_exit,
                            TONE_SUCCESS,
                        )
                    )
            for depth in range(common, len(view_path)):
                output.lines.append(
                    RenderedLine(item.no, "  " * depth + view_path[depth], TONE_SUCCESS)
                )
            current_view_path = view_path
            indent = "  " if view_path else ""

            for pre_command in implementation.pre_commands:
                output.lines.append(
                    RenderedLine(
                        item.no,
                        indent + _render_template(pre_command, entity.params),
                        TONE_SUCCESS,
                    )
                )

            tone = TONE_SUCCESS
            if not implementation.verified:
                tone = TONE_WARN
                output.warnings.append(
                    RenderWarning(item.no, f"{entity.entity_id}：{self._target_vendor} 实现未经验证")
                )
            if "intf" in entity.params and self._source_vendor and self._source_vendor != self._target_vendor:
                tone = TONE_WARN
                output.warnings.append(RenderWarning(item.no, "接口名未做厂商映射，请人工确认"))

            command = _render_template(implementation.command or "", entity.params)
            output.lines.append(RenderedLine(item.no, indent + command, tone))
            translated += 1
            if entity.entity_id not in used:
                used.append(entity.entity_id)

        if self._profile.auto_close_views and current_view_path:
            last_no = parsed_lines[-1].no if parsed_lines else 0
            for level in range(len(current_view_path), 1, -1):
                output.lines.append(
                    RenderedLine(
                        last_no,
                        "  " * (level - 1) + self._profile.view_exit,
                        TONE_SUCCESS,
                    )
                )
            output.lines.append(
                RenderedLine(last_no, self._profile.view_return, TONE_SUCCESS)
            )

        output.summary = {
            "total": len(output.lines),
            "translated": translated,
            "unsupported": unsupported,
            "duration_ms": duration_ms,
        }
        output.meta["entities_used"] = used
        return output


def _common_prefix(current: list[str], target: list[str]) -> int:
    common = 0
    while common < min(len(current), len(target)) and current[common] == target[common]:
        common += 1
    return common


def _render_template(template: str, params: dict[str, str]) -> str:
    def replace(matched: re.Match[str]) -> str:
        return params.get(matched.group(1), matched.group(0))

    return PLACEHOLDER_RE.sub(replace, template)


def _validate_parameters(spec: EntitySpec, params: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for name, parameter in spec.parameters.items():
        value = params.get(name)
        if value is None or value == "":
            if parameter.required:
                errors.append(f"缺少参数 {name}")
            continue
        if parameter.type == ParameterType.int:
            try:
                number = int(value)
            except ValueError:
                errors.append(f"参数 {name} 必须为整数")
                continue
            if parameter.range and not parameter.range[0] <= number <= parameter.range[1]:
                errors.append(
                    f"参数 {name}={number} 超出范围 {parameter.range[0]}-{parameter.range[1]}"
                )
        if parameter.format in {ValueFormat.ipv4, ValueFormat.ipv4_mask} and not _IPV4_FULL.match(value):
            errors.append(f"参数 {name} 不是合法 IPv4 地址")
        if parameter.format == ValueFormat.vlan_list and re.fullmatch(VLAN_LIST_PATTERN, value) is None:
            errors.append(f"参数 {name} 不是合法的 VLAN 列表")
        if parameter.pattern and re.fullmatch(parameter.pattern, value) is None:
            errors.append(f"参数 {name} 不符合格式要求")
    return errors
