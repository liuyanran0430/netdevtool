"""目标配置渲染：展开段与集合，合并重复段并保持对外结果结构。"""

import re
from dataclasses import dataclass, field, replace

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    Implementation,
    ParameterType,
    PreCommand,
    ValueFormat,
    VendorProfile,
    split_optional_chunks,
)
from app.translate_rule.parser import (
    IPV4_PATTERN,
    VLAN_LIST_PATTERN,
    ParsedDocument,
    ParsedEntity,
    ParsedLine,
    _view_type,
)
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
    return _TONE_BY_CONFIDENCE.get(confidence.strip().lower(), TONE_WARN)


def _degrade(tone: str, target: str) -> str:
    return target if _TONE_RANK[target] > _TONE_RANK[tone] else tone


def _warning_nos(entity: ParsedEntity) -> tuple[int, ...]:
    """实体级告警锚定自身命令行；无命令行的占位实体回退全部关联行。"""
    return tuple(entity.command_nos) if entity.command_nos else tuple(entity.source_nos)


@dataclass(frozen=True)
class RenderedLines:
    """渲染输出的一行纯文本，顺序即目标配置顺序。

    源端行号、实体归属等联动信息统一在 TranslationOutput.entity_targets 中维护。
    """

    text: str
    tone: str


@dataclass(frozen=True)
class EntityTarget:
    """单个已翻译实体的联动元数据。"""

    entity_id: str
    # 该实体覆盖的源配置行号（parser 已算干净，不含外层无关视图）
    source_nos: tuple[int, ...]
    # 实体自身命令行号（不含视图头行），前端据此区分视图行与命令行
    command_nos: tuple[int, ...] = ()
    # 该实体在目标输出中对应的行号索引（共享视图行会同时归属多个实体）
    target_line_indices: tuple[int, ...] = ()


@dataclass(frozen=True)
class RenderWarning:
    """段级告警，`no` 为该告警覆盖的全部源配置行号列表。"""

    no: tuple[int, ...]
    message: str
    code: str = "unknown"
    severity: str = "warn"


@dataclass
class TranslationOutput:
    """一次渲染的完整产物。"""

    lines: list[RenderedLines] = field(default_factory=list)
    # 与 lines 平行的源行号映射：无实体行（未识别命令、显示命令）记录其源行号，其余为 None
    line_source_nos: list[int | None] = field(default_factory=list)
    # 按实体分组的联动元数据：source_nos → 源面板高亮，target_line_indices → 目标面板高亮
    entity_targets: dict[str, EntityTarget] = field(default_factory=dict)
    warnings: list[RenderWarning] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)
    meta: dict[str, object] = field(default_factory=dict)
    parsed_lines: list[ParsedLine] = field(default_factory=list, repr=False)


@dataclass(frozen=True)
class _CandidateSegment:
    path: tuple[str, ...]
    lines: tuple[str, ...]


@dataclass
class _PreparedParams:
    params: dict[str, str]
    collections: dict[str, list[dict[str, str]]]
    has_intf: bool = False
    intf_mapped: bool = False
    intf_unmapped: bool = False


class Renderer:
    """把段级解析结果渲染为目标厂商命令。"""

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
        self._root_view = self._profile.root_view

    def render(self, document: ParsedDocument, duration_ms: int = 0) -> TranslationOutput:
        output = TranslationOutput(parsed_lines=document.lines)
        self._view_line_index: dict[tuple[str, ...], int] = {}
        self._last_entity: ParsedEntity | None = None
        # 已报过接口映射告警的目标接口名，每个接口只报一条
        self._intf_notified: set[str] = set()
        # 预创建所有实体的联动元数据；渲染过程中 target_line_indices 逐步填充。
        # 否定行等会创建同 ID 的独立实体，这里按 entity_id 合并归属取并集，
        # 使否定行与正向行联动到同一实体，避免后者覆盖前者的归属
        for entity in document.entities:
            existing = output.entity_targets.get(entity.entity_id)
            if existing is None:
                output.entity_targets[entity.entity_id] = EntityTarget(
                    entity_id=entity.entity_id,
                    source_nos=tuple(entity.source_nos),
                    command_nos=tuple(entity.command_nos),
                )
            else:
                merged_nos = sorted(set(existing.source_nos) | set(entity.source_nos))
                merged_cmds = sorted(set(existing.command_nos) | set(entity.command_nos))
                output.entity_targets[entity.entity_id] = replace(
                    existing,
                    source_nos=tuple(merged_nos),
                    command_nos=tuple(merged_cmds),
                )
        output.meta = {
            "source": {"vendor": self._source_vendor, "device_type": self._source_device_type},
            "target": {"vendor": self._target_vendor, "device_type": self._target_device_type},
        }
        for issue in document.issues:
            output.warnings.append(
                RenderWarning((issue.source_no,), issue.message, issue.code, issue.severity)
            )

        current_view_path: list[str] = []
        emitted: set[tuple[tuple[str, ...], str]] = set()
        pre_emitted: set[tuple[tuple[str, ...], str]] = set()
        entities_by_source: dict[int, list[ParsedEntity]] = {}
        for entity in document.entities:
            entities_by_source.setdefault(entity.source_no, []).append(entity)

        first_item = next(
            (item for item in document.lines if item.kind in {"command", "display", "other"}),
            None,
        )
        if first_item is not None:
            self._emit(output, RenderedLines(self._root_view, TONE_MUTED))
            current_view_path = [self._root_view]

        for item in document.lines:
            for entity in entities_by_source.get(item.no, []):
                current_view_path, _ = self._render_entity(
                    output,
                    entity,
                    current_view_path,
                    emitted,
                    pre_emitted,
                )

            if item.kind in {"view", "pre", "command"}:
                continue
            if item.kind == "display":
                actual_prefix = item.text.strip().split(maxsplit=1)[0].lower()
                tone = TONE_MUTED
                if actual_prefix != self._profile.display_prefix:
                    tone = TONE_WARN
                    output.warnings.append(
                        RenderWarning(
                            (item.no,), _DISPLAY_CHANGED_MESSAGE, "display_command", "warn"
                        )
                    )
                target_view_path = self._display_view_path(item, current_view_path)
                current_view_path = self._sync_view_path(
                    output, item.no, current_view_path, target_view_path
                )
                indent = "  " * max(0, len(current_view_path) - 1)
                self._emit(
                    output,
                    RenderedLines(
                        indent + _translate_display(item.text, self._profile),
                        tone,
                    ),
                    source_no=item.no,
                )
                continue
            if item.kind == "other":
                if current_view_path:
                    current_view_path = self._sync_view_path(
                        output, item.no, current_view_path, [self._root_view]
                    )
                self._emit(output, RenderedLines(item.text, TONE_ERROR), source_no=item.no)
                output.warnings.append(
                    RenderWarning((item.no,), "未识别的命令，已原样保留", "unknown_command", "error")
                )
                continue
            if item.kind in {"blank", "comment"}:
                # 空行与 # / ! 注释行均不进入目标配置
                continue

        if self._profile.auto_close_views and current_view_path:
            for level in range(len(current_view_path), 1, -1):
                self._emit(
                    output,
                    RenderedLines(
                        "  " * (max(0, level - 2) + 1) + self._profile.view_exit,
                        TONE_MUTED,
                    ),
                )
        if self._profile.auto_close_views and current_view_path:
            self._emit(output, RenderedLines(self._profile.view_return, TONE_MUTED))

        output.summary = {
            "total": len(output.lines),
            "duration_ms": duration_ms,
        }
        return output

    def _render_entity(
        self,
        output: TranslationOutput,
        entity: ParsedEntity,
        current_view_path: list[str],
        emitted: set[tuple[tuple[str, ...], str]],
        pre_emitted: set[tuple[tuple[str, ...], str]],
    ) -> tuple[list[str], bool]:
        spec = self._registry.get_entity(entity.entity_id)
        implementation = self._registry.resolve(
            self._target_vendor, self._target_device_type, entity.entity_id
        )
        if spec is None or implementation is None or not implementation.supported:
            self._emit(
                output,
                RenderedLines(
                    f"# 目标设备不支持: {entity.entity_id}",
                    TONE_ERROR,
                ),
                entity,
            )
            output.warnings.append(
                RenderWarning(
                    _warning_nos(entity),
                    "目标设备不支持该实体",
                    "unsupported_entity",
                    "error",
                )
            )
            return current_view_path, False
        if entity.invalid:
            self._emit(
                output,
                RenderedLines(
                    f"# 配置段冲突: {entity.entity_id}",
                    TONE_ERROR,
                ),
                entity,
            )
            return current_view_path, False

        prepared, errors = self._prepare_parameters(spec, implementation, entity, output)
        if errors:
            return current_view_path, self._invalid_entity(output, entity, errors)
        tone = self._entity_tone(output, entity, implementation)
        if prepared.has_intf:
            # 接口名被规则转换过，值得人工确认；告警只报一次并只锚定接口视图头行，命令行不因此降级
            mapped = prepared.intf_mapped and not prepared.intf_unmapped
            intf_key = prepared.params.get("intf", "")
            if intf_key and intf_key not in self._intf_notified:
                self._intf_notified.add(intf_key)
                header_nos = tuple(sorted(set(entity.source_nos) - set(entity.command_nos)))
                output.warnings.append(
                    RenderWarning(
                        header_nos or _warning_nos(entity),
                        _INTF_MAPPED_MESSAGE if mapped else _INTF_UNMAPPED_MESSAGE,
                        "intf_translated" if mapped else "intf_unmapped",
                        "warn",
                    )
                )

        if entity.negative:
            return self._render_negative(
                output, entity, implementation, prepared, current_view_path, tone
            )

        candidates, errors = self._expand_candidates(implementation, prepared)
        pre_texts, pre_errors = self._pre_command_texts(implementation, prepared.params)
        errors.extend(pre_errors)
        if errors:
            return current_view_path, self._invalid_entity(output, entity, errors)

        current_view_path = self._render_scoped_pre_commands(
            output,
            entity,
            implementation,
            pre_texts,
            current_view_path,
            emitted,
            pre_emitted,
            tone,
        )
        local_pre_done = False
        view_tone = TONE_WARN if prepared.has_intf else TONE_MUTED
        for candidate in candidates:
            target_path = [self._root_view, *candidate.path]
            current_view_path = self._sync_view_path(
                output,
                entity.source_no,
                current_view_path,
                target_path,
                new_view_tone=view_tone,
                entity=entity,
            )
            indent = "  " * max(0, len(current_view_path) - 1)
            if not local_pre_done:
                for text in pre_texts[1]:
                    key = (tuple(target_path), _normalize_command(text))
                    if key not in emitted:
                        emitted.add(key)
                        self._emit(
                            output,
                            RenderedLines(
                                indent + text,
                                tone,
                            ),
                            entity,
                        )
                local_pre_done = True
            for text in candidate.lines:
                key = (tuple(target_path), _normalize_command(text))
                if key in emitted:
                    continue
                emitted.add(key)
                self._emit(
                    output,
                    RenderedLines(
                        indent + text,
                        tone,
                    ),
                    entity,
                )
        return current_view_path, bool(candidates)

    def _prepare_parameters(
        self,
        spec: EntitySpec,
        implementation: Implementation,
        entity: ParsedEntity,
        output: TranslationOutput,
    ) -> tuple[_PreparedParams, list[str]]:
        collection_fields = {
            name for fields in spec.collections.values() for name in fields
        }
        scalar_fields = set(spec.parameters) - collection_fields
        params = _apply_param_defaults(
            spec,
            entity.params,
            entity.source_no,
            entity.entity_id,
            output,
            fields=scalar_fields,
        )
        errors = _validate_parameters(
            spec,
            params,
            allow_missing=entity.negative,
            fields=scalar_fields,
        )
        prepared = _PreparedParams(params={}, collections={})
        required_collections = {
            item.each
            for segment in implementation.segments
            for item in [segment, *segment.lines]
            if item.each
        }
        canonical_collections: dict[str, list[dict[str, str]]] = {}
        if not entity.negative:
            for collection in required_collections:
                records = entity.collections.get(collection, [])
                if not records:
                    errors.append(f"缺少集合 {collection}")
                    continue
                fields = set(spec.collections[collection])
                resolved_records = []
                for index, record in enumerate(records, start=1):
                    merged = {**entity.params, **record}
                    resolved = _apply_param_defaults(
                        spec,
                        merged,
                        entity.source_no,
                        entity.entity_id,
                        output,
                        fields=fields,
                    )
                    values = {
                        name: resolved[name] for name in fields if resolved.get(name) is not None
                    }
                    record_errors = _validate_parameters(spec, values, fields=fields)
                    errors.extend(
                        f"集合 {collection}[{index}]：{message}" for message in record_errors
                    )
                    resolved_records.append(values)
                canonical_collections[collection] = resolved_records

        prepared.params = self._convert_params(params, implementation)
        for collection, records in canonical_collections.items():
            prepared.collections[collection] = [
                self._convert_params(record, implementation) for record in records
            ]
        self._map_prepared_interfaces(prepared)
        return prepared, errors

    def _convert_params(
        self, params: dict[str, str], implementation: Implementation
    ) -> dict[str, str]:
        converted = _apply_param_formats(params, implementation.param_formats)
        return _apply_param_values(converted, implementation.param_values)

    def _map_prepared_interfaces(self, prepared: _PreparedParams) -> None:
        cross_vendor = bool(self._source_vendor and self._source_vendor != self._target_vendor)

        def map_params(params: dict[str, str]) -> dict[str, str]:
            if "intf" not in params:
                return params
            prepared.has_intf = True
            if not cross_vendor or not self._source_device_type:
                return params
            mapped, success = self._registry.map_interface(
                params["intf"],
                source_vendor=self._source_vendor or "",
                source_device_type=self._source_device_type,
                target_vendor=self._target_vendor,
                target_device_type=self._target_device_type,
            )
            prepared.intf_mapped |= success
            prepared.intf_unmapped |= not success
            return {**params, "intf": mapped}

        prepared.params = map_params(prepared.params)
        for collection, records in prepared.collections.items():
            prepared.collections[collection] = [map_params(record) for record in records]

    def _expand_candidates(
        self, implementation: Implementation, prepared: _PreparedParams
    ) -> tuple[list[_CandidateSegment], list[str]]:
        candidates: list[_CandidateSegment] = []
        errors: list[str] = []
        for segment in implementation.segments:
            segment_records = (
                prepared.collections.get(segment.each, []) if segment.each else [{}]
            )
            for segment_record in segment_records:
                params = {**prepared.params, **segment_record}
                templates = self._relative_views(segment.path)
                path = tuple(_render_template(template, params) for template in templates)
                missing = sorted(
                    {
                        name
                        for text in path
                        for name in PLACEHOLDER_RE.findall(text)
                    }
                )
                if missing:
                    errors.append(f"目标视图缺少参数 {', '.join(missing)}")
                    continue
                lines: list[str] = []
                for line in segment.lines:
                    if line.each:
                        line_records = (
                            [segment_record]
                            if segment.each == line.each
                            else prepared.collections.get(line.each, [])
                        )
                    else:
                        line_records = [{}]
                    for line_record in line_records:
                        line_params = {**params, **line_record}
                        text = _render_template(line.text, line_params)
                        if not text.strip():
                            continue
                        if PLACEHOLDER_RE.search(text):
                            missing_names = sorted(set(PLACEHOLDER_RE.findall(text)))
                            errors.append(
                                f"目标命令 {line.text} 缺少参数 {', '.join(missing_names)}"
                            )
                            continue
                        if text not in lines:
                            lines.append(text)
                candidates.append(_CandidateSegment(path, tuple(lines)))

        unique: list[_CandidateSegment] = []
        seen: set[_CandidateSegment] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            if unique and unique[-1].path == candidate.path:
                previous = unique[-1]
                lines = tuple(dict.fromkeys([*previous.lines, *candidate.lines]))
                unique[-1] = _CandidateSegment(previous.path, lines)
            else:
                unique.append(candidate)
        return unique, errors

    def _pre_command_texts(
        self, implementation: Implementation, params: dict[str, str]
    ) -> tuple[tuple[list[tuple[PreCommand, str]], list[str]], list[str]]:
        scoped: list[tuple[PreCommand, str]] = []
        local: list[str] = []
        errors: list[str] = []
        for pre in implementation.pre_commands:
            if isinstance(pre, PreCommand) and pre.view:
                text = _render_template(pre.command, params)
                if PLACEHOLDER_RE.search(text):
                    errors.append(f"前置命令缺少参数：{pre.command}")
                else:
                    scoped.append((pre, text))
            else:
                template = pre if isinstance(pre, str) else pre.command
                text = _render_template(template, params)
                if PLACEHOLDER_RE.search(text):
                    errors.append(f"前置命令缺少参数：{template}")
                else:
                    local.append(text)
        return (scoped, local), errors

    def _render_scoped_pre_commands(
        self,
        output: TranslationOutput,
        entity: ParsedEntity,
        implementation: Implementation,
        pre_texts,
        current_view_path: list[str],
        emitted: set[tuple[tuple[str, ...], str]],
        pre_emitted: set[tuple[tuple[str, ...], str]],
        tone: str,
    ) -> list[str]:
        scoped, _ = pre_texts
        for pre, text in scoped:
            target_path = [self._root_view, *self._relative_views([pre.view or ""])]
            target_path = list(dict.fromkeys(target_path))
            key = (tuple(target_path), _normalize_command(text))
            if key in pre_emitted:
                continue
            pre_emitted.add(key)
            current_view_path = self._sync_view_path(
                output, entity.source_no, current_view_path, target_path, entity=entity
            )
            self._emit(
                output,
                RenderedLines(
                    "  " * max(0, len(target_path) - 1) + text,
                    tone,
                ),
                entity,
            )
            emitted.add(key)
            current_view_path = self._sync_view_path(
                output,
                entity.source_no,
                current_view_path,
                [self._root_view],
                entity=entity,
            )
        return current_view_path

    def _render_negative(
        self,
        output: TranslationOutput,
        entity: ParsedEntity,
        implementation: Implementation,
        prepared: _PreparedParams,
        current_view_path: list[str],
        tone: str,
    ) -> tuple[list[str], bool]:
        options: list[tuple[list[str], str]] = []
        for segment in implementation.segments:
            if not segment.lines:
                if entity.negative_each is None and segment.each is None and segment.path:
                    path = self._relative_views(segment.path)
                    rendered = [_render_template(item, prepared.params) for item in path]
                    command = self._profile.negation_prefix + " " + rendered[-1]
                    options.append((rendered[:-1], command))
                continue
            for line in segment.lines:
                if entity.negative_each:
                    if line.each != entity.negative_each:
                        continue
                elif segment.each is not None or line.each is not None:
                    continue
                path = [
                    _render_template(item, prepared.params)
                    for item in self._relative_views(segment.path)
                ]
                template = line.negative_text or (
                    self._profile.negation_prefix + " " + line.text
                )
                command = _render_template(template, prepared.params)
                options.append((path, command))

        valid_options = [
            (path, command)
            for path, command in options
            if not any(PLACEHOLDER_RE.search(item) for item in [*path, command])
        ]
        if len(valid_options) != 1:
            message = (
                "无法唯一确定目标否定命令"
                if valid_options
                else "目标否定命令缺少必要参数或对应成员"
            )
            return current_view_path, self._invalid_entity(output, entity, [message])
        path, command = valid_options[0]
        target_path = [self._root_view, *path]
        current_view_path = self._sync_view_path(
            output,
            entity.source_no,
            current_view_path,
            target_path,
            new_view_tone=TONE_WARN if prepared.has_intf else TONE_MUTED,
            entity=entity,
        )
        self._emit(
            output,
            RenderedLines(
                "  " * max(0, len(target_path) - 1) + command,
                tone,
            ),
            entity,
        )
        return current_view_path, True

    def _invalid_entity(
        self, output: TranslationOutput, entity: ParsedEntity, errors: list[str]
    ) -> bool:
        message = "；".join(dict.fromkeys(errors))
        self._emit(
            output,
            RenderedLines(
                f"# 参数校验失败: {entity.entity_id}（{message}）",
                TONE_ERROR,
            ),
            entity,
        )
        output.warnings.append(
            RenderWarning(_warning_nos(entity), message, "invalid_param", "error")
        )
        return False

    def _entity_tone(
        self,
        output: TranslationOutput,
        entity: ParsedEntity,
        implementation: Implementation,
    ) -> str:
        tone = _confidence_tone(implementation.confidence)
        if self._source_vendor and self._source_device_type:
            source_impl = self._registry.resolve(
                self._source_vendor, self._source_device_type, entity.entity_id
            )
            if source_impl is not None:
                tone = _degrade(tone, _confidence_tone(source_impl.confidence))
        if implementation.origin == "supplement":
            tone = _degrade(tone, TONE_WARN)
            output.warnings.append(
                RenderWarning(
                    _warning_nos(entity),
                    f"{entity.entity_id}：命中补充知识库，结果未经验证",
                    "supplement_applied",
                    "warn",
                )
            )
        elif not implementation.verified:
            tone = _degrade(tone, TONE_WARN)
            output.warnings.append(
                RenderWarning(
                    _warning_nos(entity),
                    f"{entity.entity_id}：{self._target_vendor} 实现未经验证",
                    "unverified_impl",
                    "warn",
                )
            )
        elif implementation.confidence.strip().lower() in {"medium", "low"}:
            output.warnings.append(
                RenderWarning(
                    _warning_nos(entity),
                    f"{entity.entity_id}：目标实现置信度为 {implementation.confidence}，需人工确认",
                    "low_confidence",
                    "warn",
                )
            )
        return tone

    def _display_view_path(
        self, item: ParsedLine, current_view_path: list[str]
    ) -> list[str]:
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
            for segment in impl.segments:
                if not segment.path or _view_type(segment.path[-1]) != view_type:
                    continue
                templates = self._relative_views(segment.path)
                rendered = [_render_template(template, params) for template in templates]
                if any(PLACEHOLDER_RE.search(text) for text in rendered):
                    continue
                return [self._root_view, *rendered]
        return list(current_view_path)

    def _relative_views(self, templates: list[str]) -> list[str]:
        if templates and templates[0].strip().lower() == self._root_view:
            return list(templates[1:])
        return list(templates)

    def _emit(
        self,
        output: TranslationOutput,
        line: RenderedLines,
        entity: ParsedEntity | None = None,
        source_no: int | None = None,
    ) -> None:
        """追加输出行，把新行归属给当前实体（共享视图行可通过 `_claim_line` 事后补归属）。

        `source_no` 为无实体行（未识别命令、显示命令）的源行号，供前端行级联动。
        """
        output.lines.append(line)
        output.line_source_nos.append(source_no)
        if entity is not None:
            self._claim_line(output, len(output.lines) - 1, entity)

    def _claim_line(
        self, output: TranslationOutput, index: int, entity: ParsedEntity
    ) -> None:
        """把一条已有输出行归属给某个实体（共享视图行归并时使用）。"""
        target = output.entity_targets.get(entity.entity_id)
        if target is None:
            return
        indices = set(target.target_line_indices)
        indices.add(index)
        output.entity_targets[entity.entity_id] = replace(
            target, target_line_indices=tuple(sorted(indices))
        )

    def _sync_view_path(
        self,
        output: TranslationOutput,
        source_no: int,
        current_view_path: list[str],
        target_view_path: list[str],
        *,
        new_view_tone: str = TONE_MUTED,
        entity: ParsedEntity | None = None,
    ) -> list[str]:
        common = _common_prefix(current_view_path, target_view_path)
        # 复用已打开的视图时，把当前实体并入这些视图行的归属
        if entity is not None:
            for depth in range(1, common + 1):
                index = self._view_line_index.get(tuple(target_view_path[:depth]))
                if index is not None:
                    self._claim_line(output, index, entity)
        if not self._profile.allow_direct_view_switch:
            for level in range(len(current_view_path), common, -1):
                self._emit(
                    output,
                    RenderedLines(
                        "  " * (max(0, level - 2) + 1) + self._profile.view_exit,
                        TONE_MUTED,
                    ),
                    self._last_entity,
                )
        for depth in range(common, len(target_view_path)):
            self._emit(
                output,
                RenderedLines(
                    "  " * max(0, depth - 1) + target_view_path[depth],
                    new_view_tone if depth > 0 else TONE_MUTED,
                ),
                entity if depth > 0 else None,
            )
            if entity is not None and depth > 0:
                self._view_line_index[tuple(target_view_path[: depth + 1])] = (
                    len(output.lines) - 1
                )
        if entity is not None:
            self._last_entity = entity
        return target_view_path


def _normalize_command(text: str) -> str:
    return " ".join(text.split()).lower()


def _translate_display(text: str, profile: VendorProfile) -> str:
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
    pieces: list[str] = []
    for chunk, optional in split_optional_chunks(template):
        names = PLACEHOLDER_RE.findall(chunk)
        if optional and any(name not in params for name in names):
            continue

        def replace(matched: re.Match[str]) -> str:
            return params.get(matched.group(1), matched.group(0))

        pieces.append(PLACEHOLDER_RE.sub(replace, chunk))
    return " ".join(pieces)


def _apply_param_values(
    params: dict[str, str], mapping: dict[str, dict[str, str]]
) -> dict[str, str]:
    if not mapping:
        return params
    converted = dict(params)
    for name, values in mapping.items():
        value = converted.get(name)
        if value is None:
            continue
        target = values.get(value) or values.get(value.strip().lower())
        if target:
            converted[name] = target
    return converted


def _apply_param_formats(params: dict[str, str], formats: dict[str, str]) -> dict[str, str]:
    if not formats:
        return params
    converted = dict(params)
    for name, style in formats.items():
        value = converted.get(name)
        if value:
            converted[name] = _convert_vlan_list(value, style)
    return converted


def _convert_vlan_list(value: str, style: str) -> str:
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


def _apply_param_defaults(
    spec: EntitySpec,
    params: dict[str, str],
    source_no: int,
    entity_id: str,
    output: TranslationOutput,
    *,
    fields: set[str] | None = None,
) -> dict[str, str]:
    resolved = dict(params)
    for name, parameter in spec.parameters.items():
        if fields is not None and name not in fields:
            continue
        if name in resolved or not parameter.default:
            continue
        value = _render_template(parameter.default, resolved)
        if PLACEHOLDER_RE.search(value):
            continue
        resolved[name] = value
        output.warnings.append(
            RenderWarning(
                (source_no,),
                f"{entity_id}：参数 {name} 未提供，已按默认规则填入 {value}",
                "param_default",
                "warn",
            )
        )
    return resolved


def _validate_parameters(
    spec: EntitySpec,
    params: dict[str, str],
    *,
    allow_missing: bool = False,
    fields: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    for name, parameter in spec.parameters.items():
        if fields is not None and name not in fields:
            continue
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
