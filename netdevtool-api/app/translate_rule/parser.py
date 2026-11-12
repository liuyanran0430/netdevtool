"""源配置解析：命令模板编译为正则，并按视图状态机逐行识别实体。"""

import re
from dataclasses import dataclass

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
VLAN_LIST_PATTERN = r"\d+(?:\s+(?:to\s+\d+|,?\s*\d+))*"

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


@dataclass
class ParsedLine:
    """源配置中的一行及其识别结果。"""

    no: int
    text: str
    kind: str  # blank / comment / view / pre / command / other
    entity: ParsedEntity | None = None


def compile_template(template: str, parameters: dict[str, ParameterSpec]) -> CompiledTemplate:
    """把命令模板编译为带命名分组的正则。"""
    tokens = template.split()
    if not tokens:
        raise ValueError("模板不能为空")

    pieces: list[str] = []
    names: list[str] = []
    literal_length = 0
    for index, token in enumerate(tokens):
        token_pattern, token_literal = _compile_token(
            token, parameters, names, index == len(tokens) - 1
        )
        pieces.append(token_pattern)
        literal_length += token_literal

    pattern = re.compile(r"^\s*" + r"\s+".join(pieces) + r"\s*$", re.IGNORECASE)
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
        self._command_matchers = self._build_matchers(implementations, with_command=True)
        self._pre_matchers = self._build_matchers(implementations, with_command=False)
        self._view_matchers = self._build_view_matchers()

    def parse(self, text: str) -> list[ParsedLine]:
        parsed: list[ParsedLine] = []
        view_stack: list[tuple[str, dict[str, str]]] = []
        pending: set[str] = set()

        for number, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                parsed.append(ParsedLine(number, raw, "blank"))
                continue
            if stripped.startswith("#") or stripped.startswith("!"):
                parsed.append(ParsedLine(number, raw, "comment"))
                continue

            lowered = stripped.lower()
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

            view = self._match_view(stripped)
            if view is not None:
                template, params = view
                if _view_type(template) == "interface" and view_stack and _view_type(view_stack[-1][0]) == "interface":
                    view_stack[-1] = (template, params)
                else:
                    view_stack.append((template, params))
                pending.clear()
                parsed.append(ParsedLine(number, raw, "view"))
                continue

            context: dict[str, str] = {}
            for _, params in view_stack:
                context.update(params)
            current_view = view_stack[-1][0] if view_stack else None
            current_type = _view_type(current_view) if current_view else None

            pre = self._match(self._pre_matchers, stripped, current_type, pending or None)
            if pre is not None:
                pending.add(pre.implementation.entity_id)
                parsed.append(ParsedLine(number, raw, "pre"))
                continue

            command = self._match(self._command_matchers, stripped, current_type, pending or None)
            if command is not None:
                params = {**context, **command.template.match(stripped)}
                pending.clear()
                parsed.append(
                    ParsedLine(
                        number,
                        raw,
                        "command",
                        ParsedEntity(command.implementation.entity_id, params, current_view),
                    )
                )
                continue

            parsed.append(ParsedLine(number, raw, "other"))

        return parsed

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
            matchers.sort(key=lambda item: (-item.template.literal_length, len(item.template.param_names)))
        return buckets

    def _build_view_matchers(self) -> list[CompiledTemplate]:
        matchers: list[CompiledTemplate] = []
        seen: set[str] = set()
        for spec in self._entities.values():
            for template in spec.view_path:
                if template in seen:
                    continue
                seen.add(template)
                matchers.append(compile_template(template, spec.parameters))
        matchers.sort(key=lambda item: (-item.literal_length, len(item.param_names)))
        return matchers

    def _match_view(self, text: str) -> tuple[str, dict[str, str]] | None:
        for matcher in self._view_matchers:
            params = matcher.match(text)
            if params is not None:
                return matcher.template, params
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
