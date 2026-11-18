"""命令渲染：用目标厂商实现替换参数，并按视图层级输出。"""

import re
from dataclasses import dataclass, field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    ParameterType,
    ValueFormat,
    VendorProfile,
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
_INTF_UNMAPPED_MESSAGE = "接口名无法映射到目标厂商命名，已原样保留，请人工确认"
_INTF_MAPPED_MESSAGE = "接口名已按厂商命名规则转换，请确认映射结果"
_DISPLAY_CHANGED_MESSAGE = "显示命令关键字已转换，参数语法请按目标设备确认"


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
    # 细分原因，目前用于 unsupported_entity 的三种成因
    reason: str | None = None


@dataclass
class TranslationOutput:
    """一次渲染的完整产物。"""

    lines: list[RenderedLine] = field(default_factory=list)
    warnings: list[RenderWarning] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    meta: dict[str, object] = field(default_factory=dict)
    # 解析中间结果，供知识缺口采集使用，不对外输出
    parsed_lines: list[ParsedLine] = field(default_factory=list, repr=False)


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
        for impl in registry.implementations_for(self._target_vendor, self._target_device_type):
            templates.extend(impl.view_path)
        self._view_templates = list(dict.fromkeys(templates))
        # 目标厂商的根视图（如 system-view / configure terminal），输出时只进入一次
        self._root_view = self._profile.root_view

    def _relative_views(self, templates: list[str]) -> list[str]:
        """去掉模板里重复书写的根视图，视图路径统一从根视图之后开始。"""
        if templates and templates[0].strip().lower() == self._root_view:
            return list(templates[1:])
        return list(templates)

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
        # 翻译一开始就进入目标厂商根视图，后续只需补齐相对视图
        first_item = next(
            (
                item
                for item in parsed_lines
                if item.kind in {"command", "display", "other"}
            ),
            None,
        )
        if first_item is not None:
            output.lines.append(
                RenderedLine(first_item.no, self._root_view, TONE_MUTED)
            )
            current_view_path = [self._root_view]

        for item in parsed_lines:
            if item.kind in {"view", "pre"}:
                # 视图指令与 pre 行不直接输出，由渲染器按目标视图差异补齐
                continue
            if item.kind == "display":
                # 显示命令只替换关键字，但需要先补齐它所在的视图
                actual_prefix = item.text.strip().split(maxsplit=1)[0].lower()
                tone = TONE_MUTED
                if actual_prefix != self._profile.display_prefix:
                    tone = TONE_WARN
                    output.warnings.append(
                        RenderWarning(
                            item.no, _DISPLAY_CHANGED_MESSAGE, "display_command", "warn"
                        )
                    )
                target_view_path = self._display_view_path(item, current_view_path)
                if target_view_path != current_view_path:
                    emitted.clear()
                current_view_path = self._sync_view_path(
                    output, item, current_view_path, target_view_path
                )
                indent = (
                    "  " * max(0, len(current_view_path) - 1) if current_view_path else ""
                )
                output.lines.append(
                    RenderedLine(
                        item.no,
                        indent + _translate_display(item.text, self._profile),
                        tone,
                        item.no,
                    )
                )
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
                    current_view_path = [self._root_view]
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
                if spec is None:
                    reason = "entity_missing"
                elif implementation is None:
                    reason = "missing_impl"
                else:
                    reason = "explicit_unsupported"
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
                    RenderWarning(
                        item.no,
                        "目标设备不支持该实体",
                        "unsupported_entity",
                        "error",
                        reason,
                    )
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
            # 按目标厂商取值映射转换参数（如 stp → sstp）
            params = _apply_param_values(params, implementation.param_values)

            cross_vendor = bool(
                self._source_vendor and self._source_vendor != self._target_vendor
            )
            # 跨厂商时按接口命名表重写 intf，未识别类型则原样保留
            intf_mapped = False
            if cross_vendor and params.get("intf") and self._source_device_type:
                mapped, intf_mapped = self._registry.map_interface(
                    params["intf"],
                    source_vendor=self._source_vendor,
                    source_device_type=self._source_device_type,
                    target_vendor=self._target_vendor,
                    target_device_type=self._target_device_type,
                )
                params = {**params, "intf": mapped}

            # 厂商实现可覆盖规范视图结构（如中兴 router ospf 无 area 子视图）
            view_templates = self._relative_views(implementation.view_path)
            view_path = [
                self._root_view,
                *(_render_template(template, params) for template in view_templates),
            ]
            if not view_path and implementation.view:
                view_path = [implementation.view]

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
                # view_path[0] 是根视图，相对模板从 depth-1 开始对齐
                template = (
                    view_templates[depth - 1]
                    if 0 <= depth - 1 < len(view_templates)
                    else None
                )
                # 视图行的源行号：进入该视图的那一行，warning 也挂在该行上
                view_source_no = (
                    (item.view_nos or {}).get(_view_type(template))
                    if template is not None
                    else None
                )
                if cross_vendor and template is not None and "{intf}" in template:
                    # 接口名经过厂商转换或无法识别，均按 medium 置信度提示复核
                    view_tone = TONE_WARN
                    message, code = (
                        (_INTF_MAPPED_MESSAGE, "intf_translated")
                        if intf_mapped
                        else (_INTF_UNMAPPED_MESSAGE, "intf_unmapped")
                    )
                    output.warnings.append(
                        RenderWarning(
                            view_source_no if view_source_no is not None else item.no,
                            message,
                            code,
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
                if cross_vendor and not intf_mapped and "{intf}" in pre_command:
                    pre_tone = TONE_WARN
                    output.warnings.append(
                        RenderWarning(
                            item.no, _INTF_UNMAPPED_MESSAGE, "intf_unmapped", "warn"
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
            if implementation.origin == "supplement":
                # 补充知识库命中：结果永远降级为 warn，并标记来源
                tone = _degrade(tone, TONE_WARN)
                output.warnings.append(
                    RenderWarning(
                        item.no,
                        f"{entity.entity_id}：命中补充知识库，结果未经验证",
                        "supplement_applied",
                        "warn",
                    )
                )
            elif not implementation.verified:
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
            if cross_vendor and not intf_mapped and "{intf}" in (implementation.command or ""):
                tone = _degrade(tone, TONE_WARN)
                output.warnings.append(
                    RenderWarning(
                        item.no, _INTF_UNMAPPED_MESSAGE, "intf_unmapped", "warn"
                    )
                )

            command = _render_template(implementation.command or "", params)
            if entity.negative:
                # 否定语义：优先使用厂商的独立删除命令，否则按前缀生成，不补子命令、不进入视图
                if implementation.negative_command:
                    negative_text = _render_template(implementation.negative_command, params)
                else:
                    negative_text = self._profile.negation_prefix + " " + command
                output.lines.append(
                    RenderedLine(
                        item.no,
                        indent + negative_text,
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

    def _display_view_path(
        self, item: ParsedLine, current_view_path: list[str]
    ) -> list[str]:
        """按源视图链路定位目标厂商对应视图；无法定位时保持当前视图。"""
        if not item.view_path:
            return list(current_view_path)
        params = dict(item.view_params)
        if params.get("intf") and self._source_vendor and self._source_device_type:
            params["intf"], _ = self._registry.map_interface(
                params["intf"],
                source_vendor=self._source_vendor,
                source_device_type=self._source_device_type,
                target_vendor=self._target_vendor,
                target_device_type=self._target_device_type,
            )
        view_type = _view_type(item.view_path[-1])
        for impl in self._registry.implementations_for(
            self._target_vendor, self._target_device_type
        ):
            if (impl.view or "").strip().lower() != view_type:
                continue
            templates = self._relative_views(impl.view_path)
            rendered = [_render_template(template, params) for template in templates]
            if any(PLACEHOLDER_RE.search(text) for text in rendered):
                continue
            return [self._root_view, *rendered]
        return list(current_view_path)

    def _sync_view_path(
        self,
        output: TranslationOutput,
        item: ParsedLine,
        current_view_path: list[str],
        target_view_path: list[str],
    ) -> list[str]:
        """输出从当前视图切换到目标视图所需的退出/进入行。"""
        common = _common_prefix(current_view_path, target_view_path)
        if not self._profile.allow_direct_view_switch:
            for level in range(len(current_view_path), common, -1):
                output.lines.append(
                    RenderedLine(
                        item.no,
                        "  " * (max(0, level - 2) + 1) + self._profile.view_exit,
                        TONE_MUTED,
                    )
                )
        for depth in range(common, len(target_view_path)):
            output.lines.append(
                RenderedLine(
                    item.no,
                    "  " * max(0, depth - 1) + target_view_path[depth],
                    TONE_MUTED,
                    item.no,
                )
            )
        return target_view_path

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


def _translate_display(text: str, profile: VendorProfile) -> str:
    """把显示命令的首个关键字替换为目标厂商关键字。"""
    stripped = text.strip()
    if not stripped:
        return text
    parts = stripped.split(maxsplit=1)
    rest = f" {parts[1]}" if len(parts) > 1 else ""
    return f"{profile.display_prefix}{rest}"


def _common_prefix(current: list[str], target: list[str]) -> int:
    common = 0
    while common < min(len(current), len(target)) and current[common] == target[common]:
        common += 1
    return common


def _render_template(template: str, params: dict[str, str]) -> str:
    def replace(matched: re.Match[str]) -> str:
        return params.get(matched.group(1), matched.group(0))

    return PLACEHOLDER_RE.sub(replace, template)


def _apply_param_values(
    params: dict[str, str], mapping: dict[str, dict[str, str]]
) -> dict[str, str]:
    """按厂商实现的 param_values 转换参数取值，未配置映射的取值原样保留。"""
    if not mapping:
        return params
    converted = dict(params)
    for name, values in mapping.items():
        value = converted.get(name)
        if value is None:
            continue
        target = values.get(value)
        if target is None:
            target = values.get(value.strip().lower())
        if target:
            converted[name] = target
    return converted


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
