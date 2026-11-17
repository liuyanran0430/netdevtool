"""源配置解析：命令模板编译为正则，并按视图状态机逐行识别实体。"""

import re
from dataclasses import dataclass, field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    EntitySpec,
    Implementation,
    ParameterSpec,
    ParameterType,
    ValueFormat,
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
    bucket: str

    def match(self, text: str) -> dict[str, str] | None:
        matched = self.pattern.match(text)
        if matched is None:
            return None
        return {name: matched.group(name) for name in self.param_names}


@dataclass(frozen=True)
class SourceMatcher:
    """模板与厂商实现的绑定。"""

    implementation: Implementation
    template: CompiledTemplate


@dataclass
class ParsedEntity:
    """解析出的一条实体命令。"""

    entity_id: str
    params: dict[str, str]
    view: str | None
    negative: bool = False


@dataclass
class ParsedLine:
    """源配置中的一行及其识别结果。"""

    no: int
    text: str
    kind: str  # blank / comment / view / pre / command / display / other
    entity: ParsedEntity | None = None
    # 视图类型 -> 进入该视图的源行号，供渲染器把生成行映射回源配置
    view_nos: dict[str, int] | None = None
    # 该行所在的视图类型，未识别命令用于采集知识缺口
    view: str | None = None
    # display 行所在的源视图链路与参数，供渲染器重建目标视图
    view_path: list[str] = field(default_factory=list)
    view_params: dict[str, str] = field(default_factory=dict)


def compile_template(
    template: str, parameters: dict[str, ParameterSpec], *, prefix: bool = False
) -> CompiledTemplate:
    """把命令模板编译为带命名分组的正则。`prefix=True` 时允许匹配行首片段。"""
    tokens = template.split()
    if not tokens:
        raise ValueError("模板不能为空")

    pieces: list[str] = []
    names: list[str] = []
    literal_length = 0
    for index, token in enumerate(tokens):
        token_pattern, token_literal = _compile_token(
            token,
            parameters,
            names,
            index == len(tokens) - 1 and not prefix,
        )
        pieces.append(token_pattern)
        literal_length += token_literal

    suffix = r"(?:\s+.*)?$" if prefix else r"\s*$"
    pattern = re.compile(r"^\s*" + r"\s+".join(pieces) + suffix, re.IGNORECASE)
    first = tokens[0]
    bucket = "" if PLACEHOLDER_RE.search(first) else first.lower()
    return CompiledTemplate(template, pattern, tuple(names), literal_length, bucket)


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
    """按源设备厂商与类型解析配置文本。"""

    def __init__(self, registry: KnowledgeRegistry, vendor: str, device_type: str) -> None:
        self._entities = registry.entities
        implementations = registry.implementations_for(vendor, device_type)
        self._implementations = implementations
        profile = registry.get_profile(vendor, device_type)
        self._negation_prefix = profile.negation_prefix
        self._display_prefix = profile.display_prefix.lower()
        self._view_types: dict[str, str] = {}
        self._view_prefix_matchers: list[CompiledTemplate] = []
        self._sub_matchers: list[SourceMatcher] = []
        for impl in implementations:
            spec = self._entities.get(impl.entity_id)
            if spec is None:
                continue
            for template in impl.sub_commands:
                if template:
                    self._sub_matchers.append(
                        SourceMatcher(impl, compile_template(template, spec.parameters))
                    )
        self._sub_matchers.sort(key=_matcher_order)
        self._command_matchers = self._build_matchers(implementations, with_command=True)
        # 否定形式使用独立命令的厂商（如华三 port link-mode route）单独建立匹配表
        self._negative_matchers = self._build_negative_matchers(implementations)
        self._pre_matchers = self._build_matchers(implementations, with_command=False)
        self._view_matchers = self._build_view_matchers()

    def parse(self, text: str) -> list[ParsedLine]:
        parsed: list[ParsedLine] = []
        view_stack: list[tuple[str, dict[str, str], int]] = []
        pending: set[str] = set()

        for number, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                parsed.append(ParsedLine(number, raw, "blank"))
                continue
            if stripped.startswith("#") or stripped.startswith("!"):
                if stripped in {"#", "!"}:
                    # 单独的分节符表示配置块结束，回到系统视图
                    view_stack[:] = [("system-view", {}, -1)]
                    pending.clear()
                parsed.append(ParsedLine(number, raw, "comment"))
                continue

            lowered = stripped.lower()
            # 显示命令不参与视图状态机，也不作为配置实体解析
            if lowered.split(maxsplit=1)[0] == self._display_prefix:
                current_view = view_stack[-1][0] if view_stack else None
                current_type = (
                    self._view_type_of(current_view) if current_view else "system-view"
                )
                context: dict[str, str] = {}
                for _, params, _ in view_stack:
                    context.update(params)
                parsed.append(
                    ParsedLine(
                        number,
                        raw,
                        "display",
                        view=current_type,
                        view_path=[template for template, _, _ in view_stack],
                        view_params=context,
                    )
                )
                continue
            if lowered in VIEW_EXIT_COMMANDS:
                if view_stack:
                    view_stack.pop()
                pending.clear()
                parsed.append(ParsedLine(number, raw, "view"))
                continue
            if lowered in VIEW_TOP_COMMANDS:
                view_stack.clear()
                pending.clear()
                parsed.append(ParsedLine(number, raw, "view"))
                continue

            context: dict[str, str] = {}
            for _, params, _ in view_stack:
                context.update(params)
            current_view = view_stack[-1][0] if view_stack else None
            # 配置导出通常不带 system-view，起始行按根视图处理
            current_type = (
                self._view_type_of(current_view) if current_view else "system-view"
            )

            # 否定语义（undo / no）只按当前视图匹配实体，不参与视图进入判断
            body = stripped
            negative = False
            prefix = self._negation_prefix.lower()
            if prefix and lowered.startswith(prefix + " "):
                negative = True
                body = stripped[len(prefix) + 1 :].strip()
                command = self._match(self._command_matchers, body, current_type, pending or None)
                if command is not None:
                    params = {**context, **command.template.match(body)}
                    pending.clear()
                    parsed.append(
                        ParsedLine(
                            number,
                            raw,
                            "command",
                            ParsedEntity(
                                command.implementation.entity_id,
                                params,
                                current_view,
                                negative=True,
                            ),
                            self._view_numbers(view_stack, parsed),
                        )
                    )
                else:
                    parsed.append(ParsedLine(number, raw, "other", view=current_type))
                continue

            view = self._match_view(stripped)
            if view is not None:
                template, params = view
                entry = (template, params, len(parsed))
                if (
                    self._view_type_of(template) == "interface"
                    and view_stack
                    and self._view_type_of(view_stack[-1][0]) == "interface"
                ):
                    view_stack[-1] = entry
                else:
                    view_stack.append(entry)
                pending.clear()
                parsed.append(ParsedLine(number, raw, "view"))
                continue

            command = self._match(self._command_matchers, stripped, current_type, pending or None)
            negative = False
            if command is None:
                # 否定形式使用独立命令的厂商（如华三 port link-mode route）
                command = self._match(
                    self._negative_matchers, stripped, current_type, pending or None
                )
                negative = command is not None
            if command is None and view_stack:
                # 源配置省略 quit/分节符时，允许按根视图命令隐式退出当前视图
                command = self._match_root_command(stripped)
                if command is not None:
                    view_stack.clear()
                    context = {}
                    current_view = None
            if command is not None:
                params = {**context, **command.template.match(stripped)}
                pending.clear()
                parsed.append(
                    ParsedLine(
                        number,
                        raw,
                        "command",
                        ParsedEntity(
                            command.implementation.entity_id,
                            params,
                            current_view,
                            negative=negative,
                        ),
                        self._view_numbers(view_stack, parsed),
                    )
                )
                if current_type == "system-view":
                    # 复合命令可能同时进入子视图（如华为 ospf 1 router-id x），补齐后续行上下文
                    entry = self._match_view_entry(stripped)
                    if entry is not None:
                        view_stack.append((entry[0], entry[1], -1))
                continue

            if view_stack:
                # 视图行 + 视图内子命令合并为同一实体（如 ospf 1 换行 router-id x）
                sub = self._match_sub_command(stripped, current_view)
                if sub is not None:
                    matcher, sub_params = sub
                    entry_index = view_stack[-1][2]
                    if entry_index >= 0:
                        merged_params = {**context, **sub_params}
                        origin = parsed[entry_index]
                        parsed[entry_index] = ParsedLine(
                            origin.no,
                            origin.text,
                            "command",
                            ParsedEntity(
                                matcher.implementation.entity_id, merged_params, current_view
                            ),
                            self._view_numbers(view_stack, parsed),
                        )
                        pending.clear()
                        continue

            # 兜底：未能作为独立实体匹配的前置命令（如仅有 port link-type trunk）
            pre = self._match(self._pre_matchers, stripped, current_type, pending or None)
            if pre is not None:
                pending.add(pre.implementation.entity_id)
                parsed.append(ParsedLine(number, raw, "pre"))
                continue

            parsed.append(ParsedLine(number, raw, "other", view=current_type))

        return parsed

    def _view_numbers(
        self,
        view_stack: list[tuple[str, dict[str, str], int]],
        parsed: list[ParsedLine],
    ) -> dict[str, int]:
        """记录每一层视图的源行号，供渲染器把生成视图行映射回源配置。"""
        numbers: dict[str, int] = {}
        for template, _, index in view_stack:
            if index < 0:
                continue
            numbers[self._view_type_of(template)] = parsed[index].no
        return numbers

    def _build_matchers(
        self,
        implementations: list[Implementation],
        *,
        with_command: bool,
    ) -> dict[str, list[SourceMatcher]]:
        buckets: dict[str, list[SourceMatcher]] = {}
        for impl in implementations:
            spec = self._entities.get(impl.entity_id)
            if spec is None:
                continue
            templates = [impl.command] if with_command else impl.pre_commands
            for template in templates:
                if not template:
                    continue
                compiled = compile_template(template, spec.parameters)
                buckets.setdefault(compiled.bucket, []).append(SourceMatcher(impl, compiled))
        for matchers in buckets.values():
            matchers.sort(key=_matcher_order)
        return buckets

    def _build_negative_matchers(
        self, implementations: list[Implementation]
    ) -> dict[str, list[SourceMatcher]]:
        """为声明了 negative_command 的实现建立否定形式匹配表。"""
        buckets: dict[str, list[SourceMatcher]] = {}
        for impl in implementations:
            spec = self._entities.get(impl.entity_id)
            if spec is None or not impl.negative_command:
                continue
            compiled = compile_template(impl.negative_command, spec.parameters)
            buckets.setdefault(compiled.bucket, []).append(SourceMatcher(impl, compiled))
        for matchers in buckets.values():
            matchers.sort(key=_matcher_order)
        return buckets

    def _build_view_matchers(self) -> list[CompiledTemplate]:
        matchers: list[CompiledTemplate] = []
        seen: set[str] = set()

        def add(template: str, spec: EntitySpec, view_type: str) -> None:
            self._view_types.setdefault(template, view_type)
            if template in seen:
                return
            seen.add(template)
            matchers.append(compile_template(template, spec.parameters))
            # 行首片段匹配：用于“配置并进入视图”的复合命令（如 ospf 1 router-id x）
            self._view_prefix_matchers.append(
                compile_template(template, spec.parameters, prefix=True)
            )

        for spec in self._entities.values():
            for template in spec.view_path:
                add(template, spec, _view_type(template))

        for impl in self._implementations:
            spec = self._entities.get(impl.entity_id)
            if spec is None:
                continue
            for depth, template in enumerate(impl.view_path):
                # 厂商视图结构覆盖：沿用规范视图类型，保证 impl.view 匹配不受影响
                canonical = spec.view_path[depth] if depth < len(spec.view_path) else template
                add(template, spec, _view_type(canonical))

        matchers.sort(key=lambda item: (-item.literal_length, len(item.param_names)))
        return matchers

    def _view_type_of(self, template: str) -> str:
        return self._view_types.get(template, _view_type(template))

    def _match_view(self, text: str) -> tuple[str, dict[str, str]] | None:
        for matcher in self._view_matchers:
            params = matcher.match(text)
            if params is not None:
                return matcher.template, params
        return None

    def _match_view_entry(self, text: str) -> tuple[str, dict[str, str]] | None:
        """匹配行首的视图进入片段，用于复合命令补齐视图上下文。"""
        for matcher in self._view_prefix_matchers:
            params = matcher.match(text)
            if params is not None:
                return matcher.template, params
        return None

    def _match_sub_command(
        self, text: str, view_template: str | None
    ) -> tuple[SourceMatcher, dict[str, str]] | None:
        """匹配视图内的子命令，其所属实现的命令需以当前视图行开头。"""
        if not view_template:
            return None
        for matcher in self._sub_matchers:
            if not _starts_with(matcher.implementation.command, view_template):
                continue
            params = matcher.template.match(text)
            if params is not None:
                return matcher, params
        return None

    def _match(
        self,
        buckets: dict[str, list[SourceMatcher]],
        text: str,
        current_type: str | None,
        pending: set[str] | None,
    ) -> SourceMatcher | None:
        first = text.split(maxsplit=1)[0].lower()
        candidates = [*buckets.get(first, []), *buckets.get("", [])]
        if pending:
            matched = self._first_match(candidates, text, current_type, pending)
            if matched is not None:
                return matched
        return self._first_match(candidates, text, current_type, None)

    def _match_root_command(self, text: str) -> SourceMatcher | None:
        """匹配隶属根视图的命令，用于源配置省略视图退出指令的场景。"""
        first = text.split(maxsplit=1)[0].lower()
        candidates = [*self._command_matchers.get(first, []), *self._command_matchers.get("", [])]
        for matcher in candidates:
            impl = matcher.implementation
            spec = self._entities.get(impl.entity_id)
            if spec is None or not spec.view_path:
                continue
            if impl.view.strip().lower() != _view_type(spec.view_path[0]):
                continue
            if matcher.template.match(text) is not None:
                return matcher
        return None

    @staticmethod
    def _first_match(
        candidates: list[SourceMatcher],
        text: str,
        current_type: str | None,
        allowed_entities: set[str] | None,
    ) -> SourceMatcher | None:
        for matcher in candidates:
            impl = matcher.implementation
            if allowed_entities is not None and impl.entity_id not in allowed_entities:
                continue
            if impl.view and impl.view.strip().lower() != current_type:
                continue
            if matcher.template.match(text) is not None:
                return matcher
        return None


def _view_type(template: str) -> str:
    return template.split(maxsplit=1)[0].lower()


def _matcher_order(item: SourceMatcher) -> tuple[bool, int, int]:
    """匹配优先级：核心层优先于补充层，其次长字面量优先，最后参数少的优先。"""
    return (
        item.implementation.origin == "supplement",
        -item.template.literal_length,
        len(item.template.param_names),
    )


def _starts_with(command: str | None, prefix: str) -> bool:
    if not command:
        return False
    command_tokens = command.split()
    prefix_tokens = prefix.split()
    return (
        len(prefix_tokens) <= len(command_tokens)
        and command_tokens[: len(prefix_tokens)] == prefix_tokens
    )
