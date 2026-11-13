"""命令渲染：用目标厂商实现替换参数，并按视图层级输出。"""

import re
from dataclasses import dataclass, field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    ParameterType,
    ValueFormat,
)
from app.translate_rule.parser import IPV4_PATTERN, VLAN_LIST_PATTERN, ParsedLine, _view_type
from app.translate_rule.registry import KnowledgeRegistry

TONE_SUCCESS = "success"
TONE_WARN = "warn"
TONE_ERROR = "error"
TONE_MUTED = "muted"

_IPV4_FULL = re.compile(rf"^{IPV4_PATTERN}$")

_TONE_BY_CONFIDENCE = {"high": TONE_SUCCESS, "medium": TONE_WARN, "low": TONE_ERROR}
_TONE_RANK = {TONE_SUCCESS: 0, TONE_WARN: 1, TONE_ERROR: 2}


def _confidence_tone(confidence: str) -> str:
    """置信度映射：high → success，medium → warn，low → error。"""
    return _TONE_BY_CONFIDENCE.get(confidence.strip().lower(), TONE_WARN)


def _degrade(tone: str, target: str) -> str:
    """只允许向更严重的状态降级。"""
    return target if _TONE_RANK[target] > _TONE_RANK[tone] else tone


@dataclass(frozen=True)
class RenderedLine:
    """输出行，`no` 对齐源配置行号。"""

    no: int
    text: str
    tone: str
    # 真实源配置行号；生成行（补齐的视图/quit/return）为 None
    source_no: int | None = None
    # 该行对应的规范实体，供前端展示实体描述；视图/注释等行不关联
    entity_id: str | None = None


@dataclass(frozen=True)
class RenderWarning:
    """行级告警，供前端定位与按类型聚合。"""

    no: int
    message: str
    code: str = "unknown"
    severity: str = "warn"


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
        templates: list[str] = []
        for spec in registry.entities.values():
            templates.extend(spec.view_path)
        for impl in registry.implementations_for(self._target_vendor, self._target_device_type):
            templates.extend(impl.view_path)
        self._view_templates = list(dict.fromkeys(templates))

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
        # 当前视图内已输出的命令，用于避免前置命令与独立实体重复输出
        emitted: set[str] = set()

        for item in parsed_lines:
            if item.kind in {"view", "pre"}:
                # 视图指令与 pre 行不直接输出，由渲染器按目标视图差异补齐
                continue
            if item.kind == "other":
                # 未识别的命令原样保留，标记 error 提示人工处理
                output.lines.append(RenderedLine(item.no, item.text, TONE_ERROR, item.no))
                output.warnings.append(
                    RenderWarning(item.no, "未识别的命令，已原样保留", "unknown_command", "error")
                )
                unsupported += 1
                continue
            if item.kind in {"blank", "comment"}:
                if item.kind == "comment" and item.text.strip() in {"#", "!"} and current_view_path:
                    # 分节符已回到系统视图，后续命令无需再补齐 quit
                    current_view_path = ["system-view"]
                    emitted.clear()
                output.lines.append(RenderedLine(item.no, item.text, TONE_MUTED, item.no))
                continue

            entity = item.entity
            if entity is None:
                output.lines.append(RenderedLine(item.no, item.text, TONE_MUTED, item.no))
                continue

            spec = self._registry.get_entity(entity.entity_id)
            implementation = self._registry.resolve(
                self._target_vendor, self._target_device_type, entity.entity_id
            )
            if spec is None or implementation is None or not implementation.supported:
                output.lines.append(
                    RenderedLine(
                        item.no,
                        f"# 目标设备不支持: {entity.entity_id}",
                        TONE_ERROR,
                        item.no,
                        entity.entity_id,
                    )
                )
                output.warnings.append(
                    RenderWarning(item.no, "目标设备不支持该实体", "unsupported_entity", "error")
                )
                unsupported += 1
                continue

            errors = _validate_parameters(spec, entity.params, allow_missing=entity.negative)
            if errors:
                message = "；".join(errors)
                output.lines.append(
                    RenderedLine(
                        item.no,
                        f"# 参数校验失败: {entity.entity_id}（{message}）",
                        TONE_ERROR,
                        item.no,
                        entity.entity_id,
                    )
                )
                output.warnings.append(
                    RenderWarning(item.no, message, "invalid_param", "error")
                )
                unsupported += 1
                continue

            # 按目标厂商习惯转换参数分隔符（如 VLAN 列表 to / hyphen）
            params = _apply_param_formats(entity.params, implementation.param_formats)

            # 厂商实现可覆盖规范视图结构（如中兴 router ospf 无 area 子视图）
            view_templates = implementation.view_path or spec.view_path
            view_path = [_render_template(template, params) for template in view_templates]
            if not view_path and implementation.view:
                view_path = [implementation.view]

            cross_vendor = bool(
                self._source_vendor and self._source_vendor != self._target_vendor
            )

            common = _common_prefix(current_view_path, view_path)
            if not self._profile.allow_direct_view_switch:
                for level in range(len(current_view_path), common, -1):
                    output.lines.append(
                        RenderedLine(
                            item.no,
                            "  " * (max(0, level - 2) + 1) + self._profile.view_exit,
                            TONE_MUTED,
                        )
                    )
            for depth in range(common, len(view_path)):
                view_tone = TONE_MUTED
                # 视图行的源行号：进入该视图的那一行，warning 也挂在该行上
                view_source_no = (item.view_nos or {}).get(_view_type(view_templates[depth]))
                if (
                    cross_vendor
                    and depth < len(view_templates)
                    and "{intf}" in view_templates[depth]
                ):
                    view_tone = TONE_WARN
                    output.warnings.append(
                        RenderWarning(
                            view_source_no if view_source_no is not None else item.no,
                            "接口名未做厂商映射，请人工确认",
                            "intf_unmapped",
                            "warn",
                        )
                    )
                output.lines.append(
                    RenderedLine(
                        item.no,
                        "  " * max(0, depth - 1) + view_path[depth],
                        view_tone,
                        view_source_no,
                    )
                )
            if view_path != current_view_path:
                # 切换到其它视图后重新统计已输出命令
                emitted.clear()
            current_view_path = view_path
            indent = "  " * max(0, len(view_path) - 1) if view_path else ""

            # 删除命令只输出目标命令本身，不补前置/子命令
            for pre_command in [] if entity.negative else implementation.pre_commands:
                pre_text = _render_template(pre_command, params)
                key = _normalize_command(pre_text)
                if key in emitted:
                    # 该命令已作为独立实体输出，不再重复补前置
                    continue
                emitted.add(key)
                pre_tone = TONE_SUCCESS
                if cross_vendor and "{intf}" in pre_command:
                    pre_tone = TONE_WARN
                    output.warnings.append(
                        RenderWarning(
                            item.no, "接口名未做厂商映射，请人工确认", "intf_unmapped", "warn"
                        )
                    )
                output.lines.append(
                    RenderedLine(
                        item.no,
                        indent + pre_text,
                        pre_tone,
                        item.no,
                        entity.entity_id,
                    )
                )

            tone = _confidence_tone(implementation.confidence)
            if self._source_vendor and self._source_device_type:
                source_impl = self._registry.resolve(
                    self._source_vendor, self._source_device_type, entity.entity_id
                )
                if source_impl is not None:
                    # 两侧置信度取低值，避免源侧不确定而结果看似高可信
                    tone = _degrade(tone, _confidence_tone(source_impl.confidence))
            if not implementation.verified:
                tone = _degrade(tone, TONE_WARN)
                output.warnings.append(
                    RenderWarning(
                        item.no,
                        f"{entity.entity_id}：{self._target_vendor} 实现未经验证",
                        "unverified_impl",
                        "warn",
                    )
                )
            elif implementation.confidence.strip().lower() in {"medium", "low"}:
                output.warnings.append(
                    RenderWarning(
                        item.no,
                        f"{entity.entity_id}：目标实现置信度为 {implementation.confidence}，需人工确认",
                        "low_confidence",
                        "warn",
                    )
                )
            if cross_vendor and "{intf}" in (implementation.command or ""):
                tone = _degrade(tone, TONE_WARN)
                output.warnings.append(
                    RenderWarning(
                        item.no, "接口名未做厂商映射，请人工确认", "intf_unmapped", "warn"
                    )
                )

            command = _render_template(implementation.command or "", params)
            if entity.negative:
                # 否定语义：按目标厂商前缀输出删除命令，不补子命令、不进入视图
                output.lines.append(
                    RenderedLine(
                        item.no,
                        indent + self._profile.negation_prefix + " " + command,
                        tone,
                        item.no,
                        entity.entity_id,
                    )
                )
                translated += 1
                if entity.entity_id not in used:
                    used.append(entity.entity_id)
                continue
            output.lines.append(
                RenderedLine(item.no, indent + command, tone, item.no, entity.entity_id)
            )
            if command:
                emitted.add(_normalize_command(command))

            # 命令本身可能同时进入子视图（如 ospf 1 router-id x / router ospf 1）
            entered_view = (
                self._match_entered_view(command, params) if len(view_path) <= 1 else None
            )
            if entered_view:
                current_view_path = [*view_path, entered_view]
                inner_indent = "  " * max(0, len(current_view_path) - 1)
                for extra in implementation.sub_commands:
                    extra_text = _render_template(extra, params)
                    if PLACEHOLDER_RE.search(extra_text) or extra_text in command:
                        continue
                    output.lines.append(
                        RenderedLine(
                            item.no,
                            inner_indent + extra_text,
                            tone,
                            item.no,
                            entity.entity_id,
                        )
                    )

            translated += 1
            if entity.entity_id not in used:
                used.append(entity.entity_id)

        if self._profile.auto_close_views and current_view_path:
            last_no = parsed_lines[-1].no if parsed_lines else 0
            for level in range(len(current_view_path), 1, -1):
                output.lines.append(
                    RenderedLine(
                        last_no,
                        "  " * (max(0, level - 2) + 1) + self._profile.view_exit,
                        TONE_MUTED,
                    )
                )
            output.lines.append(
                RenderedLine(last_no, self._profile.view_return, TONE_MUTED)
            )

        output.summary = {
            "total": len(output.lines),
            "translated": translated,
            "unsupported": unsupported,
            "duration_ms": duration_ms,
        }
        output.meta["entities_used"] = used
        return output

    def _match_entered_view(self, command: str, params: dict[str, str]) -> str | None:
        """判断命令是否同时进入了某个视图，返回渲染后的视图行。"""
        tokens = command.split()
        best: str | None = None
        for template in self._view_templates:
            rendered = _render_template(template, params)
            if PLACEHOLDER_RE.search(rendered):
                continue
            parts = rendered.split()
            if len(parts) < 2 or len(parts) > len(tokens):
                continue
            if all(part.lower() == token.lower() for part, token in zip(parts, tokens)):
                if best is None or len(parts) > len(best.split()):
                    best = rendered
        return best


def _normalize_command(text: str) -> str:
    """归一化命令文本，用于当前视图内的重复输出判断。"""
    return " ".join(text.split()).lower()


def _common_prefix(current: list[str], target: list[str]) -> int:
    common = 0
    while common < min(len(current), len(target)) and current[common] == target[common]:
        common += 1
    return common


def _render_template(template: str, params: dict[str, str]) -> str:
    def replace(matched: re.Match[str]) -> str:
        return params.get(matched.group(1), matched.group(0))

    return PLACEHOLDER_RE.sub(replace, template)


def _apply_param_formats(params: dict[str, str], formats: dict[str, str]) -> dict[str, str]:
    """按厂商实现的 param_formats 转换参数取值形态。"""
    if not formats:
        return params
    converted = dict(params)
    for name, style in formats.items():
        value = converted.get(name)
        if value:
            converted[name] = _convert_vlan_list(value, style)
    return converted


def _convert_vlan_list(value: str, style: str) -> str:
    """在 to（如 10 to 20）与 hyphen（如 10-20,30）两种 VLAN 列表写法之间转换。"""
    groups = _split_vlan_groups(value)
    if not groups:
        return value
    if style == "to":
        return " ".join(f"{start} to {end}" if end else start for start, end in groups)
    return ",".join(f"{start}-{end}" if end else start for start, end in groups)


def _split_vlan_groups(value: str) -> list[tuple[str, str | None]]:
    tokens = [token for token in re.split(r"[,\s]+", value.strip()) if token]
    groups: list[tuple[str, str | None]] = []
    index = 0
    while index < len(tokens):
        current = tokens[index]
        if index + 2 < len(tokens) and tokens[index + 1].lower() == "to":
            groups.append((current, tokens[index + 2]))
            index += 3
            continue
        if current.count("-") == 1:
            start, end = current.split("-")
            groups.append((start, end))
            index += 1
            continue
        groups.append((current, None))
        index += 1
    return groups


def _validate_parameters(
    spec: EntitySpec, params: dict[str, str], *, allow_missing: bool = False
) -> list[str]:
    errors: list[str] = []
    for name, parameter in spec.parameters.items():
        value = params.get(name)
        if value is None or value == "":
            if parameter.required and not allow_missing:
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
