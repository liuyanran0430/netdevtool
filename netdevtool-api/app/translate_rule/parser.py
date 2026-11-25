"""源配置解析：按配置段识别实体，聚合同对象并保留扁平行视图。"""

import re
from dataclasses import dataclass, field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    Implementation,
    LineSpec,
    ParameterSpec,
    ParameterType,
    SegmentSpec,
    ValueFormat,
    split_optional_chunks,
)
from app.translate_rule.registry import KnowledgeRegistry

IPV4_PATTERN = r"\d{1,3}(?:\.\d{1,3}){3}"
VLAN_LIST_PATTERN = r"\d+(?:(?:\s*[-,]\s*|\s+)\d+)*(?:\s+to\s+\d+(?:\s+\d+)*)?"

VIEW_EXIT_COMMANDS = {"quit", "exit"}
VIEW_TOP_COMMANDS = {"return", "end"}


@dataclass(frozen=True)
class CompiledTemplate:
    """编译后的命令模板。"""

    template: str
    pattern: re.Pattern[str]
    param_names: tuple[str, ...]
    literal_length: int

    def match(self, text: str) -> dict[str, str] | None:
        matched = self.pattern.match(text)
        if matched is None:
            return None
        params: dict[str, str] = {}
        for name in self.param_names:
            value = matched.group(name)
            if value is not None:
                params[name] = value
        return params


@dataclass
class ParsedEntity:
    """一个逻辑配置对象；集合字段与普通单值参数分开保存。"""

    entity_id: str
    params: dict[str, str]
    view: str | None
    negative: bool = False
    collections: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    source_nos: list[int] = field(default_factory=list)
    # 实体自身命令行号（不含视图头），决定渲染位置；视图头行号只进 source_nos
    command_nos: list[int] = field(default_factory=list)
    negative_each: str | None = None
    invalid: bool = False

    @property
    def source_no(self) -> int:
        if self.command_nos:
            return min(self.command_nos)
        return min(self.source_nos) if self.source_nos else 0


@dataclass
class ParsedLine:
    """源配置中的一行及其识别结果。"""

    no: int
    text: str
    kind: str  # blank / comment / view / pre / command / display / other
    entity: ParsedEntity | None = None
    view: str | None = None
    view_path: list[str] = field(default_factory=list)
    view_params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedIssue:
    """源段聚合阶段发现的问题，由渲染器转换为对外告警。"""

    source_no: int
    message: str
    code: str
    severity: str = "error"


@dataclass
class ParsedDocument:
    """段级逻辑对象与原始顺序行视图。"""

    lines: list[ParsedLine] = field(default_factory=list)
    entities: list[ParsedEntity] = field(default_factory=list)
    issues: list[ParsedIssue] = field(default_factory=list)


@dataclass(frozen=True)
class _SegmentRule:
    implementation: Implementation
    spec: EntitySpec
    segment: SegmentSpec
    index: int


@dataclass(frozen=True)
class _LineMatcher:
    rule: _SegmentRule
    line: LineSpec
    index: int
    template: CompiledTemplate


@dataclass(frozen=True)
class _PathMatcher:
    rule: _SegmentRule
    template: CompiledTemplate
    depth: int
    parent_types: tuple[str, ...]


@dataclass
class _ViewEntry:
    template: str
    params: dict[str, str]
    line_index: int
    rules: list[_SegmentRule]
    # 段头自身可成实体的规则：无成员命中时在解析末尾补建实体
    header_rules: list[_SegmentRule] = field(default_factory=list)
    context: dict[str, str] = field(default_factory=dict)
    # 该视图所在的完整视图栈行号，供实体记录“包括外层视图”的所有行
    stack_nos: tuple[int, ...] = ()
    # 在该视图内识别出的实体，用于把 quit 行归属到对应实体
    entities: list[ParsedEntity] = field(default_factory=list)


def compile_template(
    template: str, parameters: dict[str, ParameterSpec], *, prefix: bool = False
) -> CompiledTemplate:
    """把命令模板编译为带命名分组的正则。

    `[ ... ]` 包裹的片段视为可省略部分，`prefix=True` 时允许匹配行首片段。
    """
    flat: list[tuple[str, bool]] = []
    for chunk, optional in split_optional_chunks(template):
        for token in chunk.split():
            flat.append((token, optional))
    if not flat:
        raise ValueError("模板不能为空")

    groups: list[tuple[bool, list[str]]] = []
    for token, optional in flat:
        if groups and groups[-1][0] == optional:
            groups[-1][1].append(token)
        else:
            groups.append((optional, [token]))

    pieces: list[str] = []
    names: list[str] = []
    literal_length = 0
    emitted = False
    cursor = 0
    last_index = len(flat) - 1
    for optional, tokens in groups:
        token_pieces: list[str] = []
        for token in tokens:
            is_last = cursor == last_index and not prefix
            token_pattern, token_literal = _compile_token(
                token, parameters, names, is_last
            )
            token_pieces.append(token_pattern)
            literal_length += token_literal
            cursor += 1
        body = r"\s+".join(token_pieces)
        if optional:
            pieces.append(rf"(?:\s+{body})?")
            continue
        pieces.append((r"\s+" if emitted else "") + body)
        emitted = True

    suffix = r"(?:\s+.*)?$" if prefix else r"\s*$"
    pattern = re.compile(r"^\s*" + "".join(pieces) + suffix, re.IGNORECASE)
    return CompiledTemplate(template, pattern, tuple(names), literal_length)


def _compile_token(
    token: str,
    parameters: dict[str, ParameterSpec],
    names: list[str],
    is_last: bool,
) -> tuple[str, int]:
    if PLACEHOLDER_RE.fullmatch(token):
        name = token[1:-1]
        return _param_pattern(name, parameters, names, is_last), 0

    pieces: list[str] = []
    literal_length = 0
    cursor = 0
    for matched in PLACEHOLDER_RE.finditer(token):
        literal = token[cursor : matched.start()]
        pieces.append(re.escape(literal))
        literal_length += len(literal)
        pieces.append(_param_pattern(matched.group(1), parameters, names, False))
        cursor = matched.end()
    tail = token[cursor:]
    pieces.append(re.escape(tail))
    literal_length += len(tail)
    return "".join(pieces), literal_length


def _param_pattern(
    name: str,
    parameters: dict[str, ParameterSpec],
    names: list[str],
    is_last: bool,
) -> str:
    if name in names:
        return f"(?P={name})"
    names.append(name)

    spec = parameters.get(name)
    if spec and spec.pattern:
        return f"(?P<{name}>{spec.pattern})"

    param_format = spec.format if spec else None
    if param_format == ValueFormat.vlan_list:
        return f"(?P<{name}>{VLAN_LIST_PATTERN})"
    if param_format in {ValueFormat.ipv4, ValueFormat.ipv4_mask}:
        return f"(?P<{name}>{IPV4_PATTERN})"

    param_type = spec.type if spec else ParameterType.string
    if param_type == ParameterType.int:
        return f"(?P<{name}>\\d+)"
    return f"(?P<{name}>.+)" if is_last else f"(?P<{name}>\\S+)"


class SourceParser:
    """按源厂商的段模板识别配置，并按 key 聚合逻辑对象。"""

    def __init__(self, registry: KnowledgeRegistry, vendor: str, device_type: str) -> None:
        self._entities = registry.entities
        self._implementations = registry.implementations_for(vendor, device_type)
        profile = registry.get_profile(vendor, device_type)
        self._root_view = profile.root_view
        self._root_view_type = _view_type(profile.root_view)
        self._negation_prefix = profile.negation_prefix
        self._display_prefix = profile.display_prefix.lower()

        self._rules: list[_SegmentRule] = []
        self._path_matchers: list[_PathMatcher] = []
        self._line_matchers: list[_LineMatcher] = []
        self._negative_line_matchers: list[_LineMatcher] = []
        self._pre_matchers: list[CompiledTemplate] = []
        for impl in self._implementations:
            spec = self._entities.get(impl.entity_id)
            if spec is None:
                continue
            parameters = self._parameters_for(impl, spec)
            for index, segment in enumerate(impl.segments):
                rule = _SegmentRule(impl, spec, segment, index)
                self._rules.append(rule)
                for depth, template in enumerate(segment.path):
                    self._path_matchers.append(
                        _PathMatcher(
                            rule,
                            compile_template(template, parameters),
                            depth,
                            tuple(_view_type(item) for item in segment.path[:depth]),
                        )
                    )
                for line_index, line in enumerate(segment.lines):
                    templates = [line.text, *line.aliases]
                    for template in templates:
                        self._line_matchers.append(
                            _LineMatcher(
                                rule,
                                line,
                                line_index,
                                compile_template(template, parameters),
                            )
                        )
                    if line.negative_text:
                        self._negative_line_matchers.append(
                            _LineMatcher(
                                rule,
                                line,
                                line_index,
                                compile_template(line.negative_text, parameters),
                            )
                        )
            for pre in impl.pre_commands:
                template = pre if isinstance(pre, str) else pre.command
                self._pre_matchers.append(compile_template(template, parameters))

        self._path_matchers.sort(key=lambda item: _template_order(item.rule, item.template))
        self._line_matchers.sort(key=lambda item: _template_order(item.rule, item.template))
        self._negative_line_matchers.sort(
            key=lambda item: _template_order(item.rule, item.template)
        )

    def parse(self, text: str) -> ParsedDocument:
        document = ParsedDocument()
        view_stack: list[_ViewEntry] = []
        view_entries: list[_ViewEntry] = []
        groups: dict[tuple[object, ...], ParsedEntity] = {}
        occurrence = 0
        issue_keys: set[tuple[int, str, str]] = set()

        def add_issue(no: int, code: str, message: str) -> None:
            key = (no, code, message)
            if key in issue_keys:
                return
            issue_keys.add(key)
            document.issues.append(ParsedIssue(no, message, code))

        for number, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                document.lines.append(ParsedLine(number, raw, "blank"))
                continue
            if stripped.startswith("#") or stripped.startswith("!"):
                if stripped in {"#", "!"}:
                    view_stack.clear()
                document.lines.append(ParsedLine(number, raw, "comment"))
                continue

            lowered = stripped.lower()
            if lowered.split(maxsplit=1)[0] == self._display_prefix:
                document.lines.append(
                    ParsedLine(
                        number,
                        raw,
                        "display",
                        view=self._current_view_type(view_stack),
                        view_path=[entry.template for entry in view_stack],
                        view_params=self._context(view_stack),
                    )
                )
                continue
            if lowered in VIEW_EXIT_COMMANDS:
                if view_stack:
                    closed = view_stack.pop()
                    for entity in closed.entities:
                        if number not in entity.source_nos:
                            entity.source_nos.append(number)
                document.lines.append(ParsedLine(number, raw, "view"))
                continue
            if lowered in VIEW_TOP_COMMANDS or lowered == self._root_view:
                view_stack.clear()
                document.lines.append(ParsedLine(number, raw, "view"))
                continue

            matched = self._match_negative_member(
                stripped, raw, number, view_stack, document, groups, add_issue
            )
            if not matched:
                matched = self._match_view(
                    stripped,
                    raw,
                    number,
                    view_stack,
                    view_entries,
                    document,
                    groups,
                    add_issue,
                )
            if not matched:
                matched = self._match_member(
                    stripped,
                    raw,
                    number,
                    view_stack,
                    document,
                    groups,
                    add_issue,
                    negative=False,
                )
            if not matched and self._has_negation_prefix(stripped):
                body = stripped[len(self._negation_prefix) + 1 :].strip()
                matched = self._match_member(
                    body,
                    raw,
                    number,
                    view_stack,
                    document,
                    groups,
                    add_issue,
                    negative=True,
                )
                if not matched:
                    matched = self._match_negative_path(
                        body, raw, number, view_stack, document
                    )

            if not matched and view_stack:
                # 配置省略 quit 时，只有确实命中根视图规则才隐式退出。
                saved_stack = view_stack[:]
                view_stack.clear()
                matched = self._match_negative_member(
                    stripped, raw, number, view_stack, document, groups, add_issue
                )
                if not matched:
                    matched = self._match_view(
                        stripped,
                        raw,
                        number,
                        view_stack,
                        view_entries,
                        document,
                        groups,
                        add_issue,
                    )
                if not matched:
                    matched = self._match_member(
                        stripped,
                        raw,
                        number,
                        view_stack,
                        document,
                        groups,
                        add_issue,
                        negative=False,
                    )
                if not matched and self._has_negation_prefix(stripped):
                    body = stripped[len(self._negation_prefix) + 1 :].strip()
                    matched = self._match_member(
                        body,
                        raw,
                        number,
                        view_stack,
                        document,
                        groups,
                        add_issue,
                        negative=True,
                    )
                    if not matched:
                        matched = self._match_negative_path(
                            body, raw, number, view_stack, document
                        )
                if not matched:
                    view_stack[:] = saved_stack

            if matched:
                occurrence += 1
                continue
            if any(matcher.match(stripped) is not None for matcher in self._pre_matchers):
                document.lines.append(
                    ParsedLine(number, raw, "pre", view=self._current_view_type(view_stack))
                )
                continue
            document.lines.append(
                ParsedLine(
                    number,
                    raw,
                    "other",
                    view=self._current_view_type(view_stack),
                )
            )

        # 完整段头存在、但没有任何成员或段头实体命中时，不作为已识别视图吞掉。
        for entry in view_entries:
            line = document.lines[entry.line_index]
            if line.kind != "view":
                continue
            if entry.header_rules:
                self._create_header_entities(
                    entry, line, document, groups, add_issue
                )
                continue
            if entry.rules:
                line.kind = "other"
                line.view = _view_type(entry.template)

        document.entities.sort(key=lambda entity: entity.source_no)
        return document

    def _create_header_entities(
        self,
        entry: _ViewEntry,
        line: ParsedLine,
        document: ParsedDocument,
        groups: dict[tuple[object, ...], ParsedEntity],
        add_issue,
    ) -> None:
        """段头匹配但无成员命中时，按段头参数补建实体。"""
        for rule in entry.header_rules:
            entity = self._recognize(
                rule,
                entry.context,
                line.no,
                line.view,
                document,
                groups,
                add_issue,
                negative=False,
            )
            self._collect_for_segment(rule, entity, entry.context, line.no, add_issue)
            path_depth = len(rule.segment.path)
            nos_to_add = (
                entry.stack_nos[-path_depth:]
                if 0 < path_depth < len(entry.stack_nos)
                else entry.stack_nos
            )
            for header_no in nos_to_add:
                if header_no not in entity.source_nos:
                    entity.source_nos.append(header_no)
            if entity not in entry.entities:
                entry.entities.append(entity)
            if line.entity is None:
                line.kind = "command"
                line.entity = entity

    def _match_view(
        self,
        text: str,
        raw: str,
        no: int,
        stack: list[_ViewEntry],
        entries: list[_ViewEntry],
        document: ParsedDocument,
        groups: dict[tuple[object, ...], ParsedEntity],
        add_issue,
    ) -> bool:
        depth = len(stack)
        parent_types = tuple(_view_type(entry.template) for entry in stack)
        candidates = [
            matcher
            for matcher in self._path_matchers
            if matcher.depth == depth and matcher.parent_types == parent_types
        ]
        replace = False
        if stack:
            # 同一层同类视图可直接切换，主要用于连续 interface 段。
            sibling_parent_types = parent_types[:-1]
            candidates.extend(
                matcher
                for matcher in self._path_matchers
                if matcher.depth == depth - 1
                and matcher.parent_types == sibling_parent_types
                and _view_type(matcher.template.template) == _view_type(stack[-1].template)
            )
        candidates.sort(key=lambda item: _template_order(item.rule, item.template))

        selected: _PathMatcher | None = None
        params: dict[str, str] | None = None
        for matcher in candidates:
            matched = matcher.template.match(text)
            if matched is None:
                continue
            selected = matcher
            params = matched
            replace = matcher.depth == depth - 1
            break
        if selected is None or params is None:
            return False

        template = selected.template.template
        rules = [
            matcher.rule
            for matcher in candidates
            if matcher.depth == selected.depth
            and matcher.parent_types == selected.parent_types
            and matcher.template.template == template
            and len(matcher.rule.segment.path) == selected.depth + 1
        ]
        rules = list({id(rule): rule for rule in rules}.values())
        normalized = self._normalize_params(selected.rule.implementation, params)
        entry = _ViewEntry(template, normalized, len(document.lines), rules)
        if replace:
            stack[-1] = entry
        else:
            stack.append(entry)
        entries.append(entry)

        line = ParsedLine(no, raw, "view", view=_view_type(template))
        document.lines.append(line)
        context = self._context(stack)
        entry.context = context
        entry.stack_nos = tuple(document.lines[item.line_index].no for item in stack)
        for rule in rules:
            if rule.segment.lines:
                if rule.segment.header_entity:
                    entry.header_rules.append(rule)
                continue
            entity = self._recognize(
                rule,
                context,
                no,
                template,
                document,
                groups,
                add_issue,
                negative=False,
            )
            self._collect_for_segment(rule, entity, context, no, add_issue)
            # 只加与 segment.path 相关的尾部栈层行号，避免外层无关视图（如 interface 层）
            path_depth = len(rule.segment.path)
            nos_to_add = (
                entry.stack_nos[-path_depth:]
                if 0 < path_depth < len(entry.stack_nos)
                else entry.stack_nos
            )
            for header_no in nos_to_add:
                if header_no not in entity.source_nos:
                    entity.source_nos.append(header_no)
            self._bind_entity(stack, entity)
            if line.entity is None:
                line.kind = "command"
                line.entity = entity
        return True

    def _match_member(
        self,
        text: str,
        raw: str,
        no: int,
        stack: list[_ViewEntry],
        document: ParsedDocument,
        groups: dict[tuple[object, ...], ParsedEntity],
        add_issue,
        *,
        negative: bool,
    ) -> bool:
        for matcher in self._line_matchers:
            if not self._path_matches(matcher.rule.segment.path, stack):
                continue
            params = matcher.template.match(text)
            if params is None:
                continue
            rule = matcher.rule
            merged = {
                **self._context(stack),
                **self._normalize_params(rule.implementation, params),
            }
            entity = self._recognize(
                rule,
                merged,
                no,
                stack[-1].template if stack else None,
                document,
                groups,
                add_issue,
                negative=negative,
                negative_each=matcher.line.each or rule.segment.each,
                collection_names={rule.segment.each, matcher.line.each},
            )
            if not negative:
                self._collect_for_segment(rule, entity, merged, no, add_issue)
                if matcher.line.each:
                    self._add_collection(
                        entity,
                        rule.spec,
                        matcher.line.each,
                        merged,
                        no,
                        add_issue,
                    )
            line = ParsedLine(
                no,
                raw,
                "command",
                entity,
                self._current_view_type(stack),
            )
            document.lines.append(line)
            self._claim_header(
                stack,
                entity,
                document,
                include_source=True,
                path_depth=len(rule.segment.path),
            )
            self._bind_entity(stack, entity)
            return True
        return False

    def _match_negative_member(
        self,
        text: str,
        raw: str,
        no: int,
        stack: list[_ViewEntry],
        document: ParsedDocument,
        groups: dict[tuple[object, ...], ParsedEntity],
        add_issue,
    ) -> bool:
        for matcher in self._negative_line_matchers:
            if not self._path_matches(matcher.rule.segment.path, stack):
                continue
            params = matcher.template.match(text)
            if params is None:
                continue
            rule = matcher.rule
            merged = {
                **self._context(stack),
                **self._normalize_params(rule.implementation, params),
            }
            entity = self._recognize(
                rule,
                merged,
                no,
                stack[-1].template if stack else None,
                document,
                groups,
                add_issue,
                negative=True,
                negative_each=matcher.line.each or rule.segment.each,
            )
            document.lines.append(
                ParsedLine(
                    no,
                    raw,
                    "command",
                    entity,
                    self._current_view_type(stack),
                )
            )
            self._claim_header(stack, entity, document, include_source=True)
            return True
        return False

    def _match_negative_path(
        self,
        text: str,
        raw: str,
        no: int,
        stack: list[_ViewEntry],
        document: ParsedDocument,
    ) -> bool:
        depth = len(stack)
        parent_types = tuple(_view_type(entry.template) for entry in stack)
        for matcher in self._path_matchers:
            if matcher.depth != depth or matcher.parent_types != parent_types:
                continue
            if matcher.rule.segment.lines or len(matcher.rule.segment.path) != depth + 1:
                continue
            params = matcher.template.match(text)
            if params is None:
                continue
            merged = {**self._context(stack), **params}
            entity = ParsedEntity(
                matcher.rule.implementation.entity_id,
                merged,
                stack[-1].template if stack else None,
                negative=True,
                source_nos=[no],
            )
            document.entities.append(entity)
            document.lines.append(
                ParsedLine(
                    no,
                    raw,
                    "command",
                    entity,
                    self._current_view_type(stack),
                )
            )
            return True
        return False

    def _recognize(
        self,
        rule: _SegmentRule,
        params: dict[str, str],
        no: int,
        view: str | None,
        document: ParsedDocument,
        groups: dict[tuple[object, ...], ParsedEntity],
        add_issue,
        *,
        negative: bool,
        negative_each: str | None = None,
        collection_names: set[str | None] | None = None,
    ) -> ParsedEntity:
        collection_fields: set[str] = set()
        if not negative:
            names = collection_names or {rule.segment.each}
            for collection in names:
                if collection:
                    collection_fields.update(rule.spec.collections.get(collection, []))
        scalar = {
            name: value
            for name, value in params.items()
            if negative or name not in collection_fields
        }
        if negative:
            entity = ParsedEntity(
                rule.implementation.entity_id,
                scalar,
                view,
                negative=True,
                negative_each=negative_each,
                source_nos=[no],
                command_nos=[no],
            )
            document.entities.append(entity)
            return entity

        key_fields = rule.segment.key
        if key_fields and all(params.get(name) is not None for name in key_fields):
            group_key: tuple[object, ...] = (
                rule.implementation.entity_id,
                *((name, params[name]) for name in key_fields),
            )
        else:
            group_key = (rule.implementation.entity_id, "occurrence", len(document.entities))
        entity = groups.get(group_key)
        if entity is None:
            entity = ParsedEntity(
                rule.implementation.entity_id,
                dict(scalar),
                view,
                source_nos=[no],
                command_nos=[no],
            )
            groups[group_key] = entity
            document.entities.append(entity)
            return entity

        for name, value in scalar.items():
            previous = entity.params.get(name)
            if previous is None:
                entity.params[name] = value
            elif previous != value:
                entity.invalid = True
                add_issue(
                    no,
                    "param_conflict",
                    f"{entity.entity_id}：参数 {name} 冲突，保留 {previous}，忽略 {value}",
                )
        if no not in entity.source_nos:
            entity.source_nos.append(no)
        if no not in entity.command_nos:
            entity.command_nos.append(no)
        return entity

    def _collect_for_segment(self, rule, entity, params, no, add_issue) -> None:
        if rule.segment.each:
            self._add_collection(
                entity, rule.spec, rule.segment.each, params, no, add_issue
            )

    @staticmethod
    def _add_collection(entity, spec, collection, params, no, add_issue) -> None:
        fields = spec.collections[collection]
        record = {name: params[name] for name in fields if params.get(name) is not None}
        records = entity.collections.setdefault(collection, [])
        if record in records:
            return
        if len(record) < len(fields):
            compatible = []
            for index, previous in enumerate(records):
                if len(previous) == len(fields):
                    continue
                if any(
                    name in previous and previous[name] != value
                    for name, value in record.items()
                ):
                    continue
                merged = {**previous, **record}
                if len(merged) == len(fields):
                    compatible.append((index, merged))
            if len(compatible) == 1:
                index, merged = compatible[0]
                records[index] = merged
                return
            if len(compatible) > 1:
                add_issue(
                    no,
                    "ambiguous_collection",
                    f"{entity.entity_id}：集合 {collection} 无法唯一关联字段，未自动组合",
                )
        records.append(record)

    @staticmethod
    def _bind_entity(stack: list[_ViewEntry], entity: ParsedEntity) -> None:
        """把实体绑定到其所在的整条视图栈，quit 行据此归属。"""
        for entry in stack:
            if entity not in entry.entities:
                entry.entities.append(entity)

    @staticmethod
    def _claim_header(
        stack: list[_ViewEntry],
        entity: ParsedEntity,
        document: ParsedDocument,
        *,
        include_source: bool,
        path_depth: int = 0,
    ) -> None:
        """把实体绑定到其所在的整条视图栈，并把段头视图行转成命令实体行。

        include_source=True 时只把与该实体 segment.path 相关的尾部栈层行号加入 source_nos，
        避免无关的外层视图（如 interface 层）被一并纳入。
        """
        if not stack:
            return
        entry = stack[-1]
        line = document.lines[entry.line_index]
        if line.kind == "view":
            line.kind = "command"
            line.entity = entity
        if not include_source:
            return
        if path_depth <= 0 or path_depth >= len(stack):
            for item in stack:
                header_no = document.lines[item.line_index].no
                if header_no not in entity.source_nos:
                    entity.source_nos.append(header_no)
            return
        # 只把尾部 path_depth 层的 header 行号纳入（与该 segment.path 直接相关的视图）
        for item in stack[-path_depth:]:
            header_no = document.lines[item.line_index].no
            if header_no not in entity.source_nos:
                entity.source_nos.append(header_no)

    @staticmethod
    def _context(stack) -> dict[str, str]:
        context: dict[str, str] = {}
        for entry in stack:
            context.update(entry.params)
        return context

    def _current_view_type(self, stack) -> str:
        if not stack:
            return self._root_view_type
        return _view_type(stack[-1].template)

    @staticmethod
    def _path_matches(path: list[str], stack: list[_ViewEntry]) -> bool:
        if len(path) != len(stack):
            return False
        return all(
            _compatible_template(entry.template, template)
            for entry, template in zip(stack, path)
        )

    def _has_negation_prefix(self, text: str) -> bool:
        prefix = self._negation_prefix.lower()
        return bool(prefix and text.lower().startswith(prefix + " "))

    @staticmethod
    def _parameters_for(
        impl: Implementation, spec: EntitySpec
    ) -> dict[str, ParameterSpec]:
        """把厂商取值别名并入参数正则，便于识别源配置中的厂商特有取值。"""
        if not impl.param_values or not spec.parameters:
            return spec.parameters
        parameters = dict(spec.parameters)
        for name, mapping in impl.param_values.items():
            parameter = parameters.get(name)
            aliases = [
                re.escape(str(value))
                for value in mapping.values()
                if str(value).strip()
            ]
            if parameter is None or not parameter.pattern or not aliases:
                continue
            parameters[name] = parameter.model_copy(
                update={"pattern": f"(?:{parameter.pattern}|{'|'.join(aliases)})"}
            )
        return parameters

    @staticmethod
    def _normalize_params(
        impl: Implementation, params: dict[str, str]
    ) -> dict[str, str]:
        """把厂商取值的别名还原为规范取值，再交给渲染器映射。"""
        if not impl.param_values:
            return params
        normalized = dict(params)
        for name, mapping in impl.param_values.items():
            value = normalized.get(name)
            if value is None:
                continue
            lowered = value.strip().lower()
            if lowered in {str(key).strip().lower() for key in mapping}:
                continue
            for canonical, vendor_value in mapping.items():
                if lowered == str(vendor_value).strip().lower():
                    normalized[name] = canonical
                    break
        return normalized


def _template_order(rule: _SegmentRule, template: CompiledTemplate) -> tuple:
    return (
        rule.implementation.origin == "supplement",
        -template.literal_length,
        len(template.param_names),
    )


def _compatible_template(actual: str, expected: str) -> bool:
    if actual == expected:
        return True
    if _view_type(actual) != _view_type(expected):
        return False
    actual_literals = _literal_tokens(actual)
    expected_literals = _literal_tokens(expected)
    position = 0
    for literal in expected_literals:
        try:
            position = actual_literals.index(literal, position) + 1
        except ValueError:
            return False
    return True


def _literal_tokens(template: str) -> list[str]:
    return [
        literal
        for token in template.replace("[", "").replace("]", "").split()
        if (literal := PLACEHOLDER_RE.sub("", token).lower())
    ]


def _view_type(template: str) -> str:
    return template.replace("[", "").replace("]", "").split(maxsplit=1)[0].lower()
