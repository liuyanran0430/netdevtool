"""LLM 候选命令契约与自动校验。

校验不信任模型自报置信度，只依据模板回放、参数覆盖、渲染冒烟与视图白名单。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.translate_rule.models import (
    PLACEHOLDER_RE,
    ParameterSpec,
    ParameterType,
    ValueFormat,
    extract_placeholders,
)
from app.translate_rule.parser import compile_template
from app.translate_rule.registry import KnowledgeRegistry

SENSITIVE_KEYWORDS = ("password", "cipher", "secret", "community", "key")
_IPV4_RE = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
_DIGITS_RE = re.compile(r"\d+")


class CandidateParameter(BaseModel):
    """候选命令的参数声明。"""

    model_config = ConfigDict(extra="ignore")

    type: str = "string"
    format: str | None = None
    required: bool = True
    pattern: str | None = None
    note: str | None = None


class CandidatePayload(BaseModel):
    """LLM 返回的候选 JSON。"""

    model_config = ConfigDict(extra="ignore")

    status: str = "unknown"
    source_template: str = ""
    source_view_path: list[str] = Field(default_factory=list)
    parameters: dict[str, CandidateParameter] = Field(default_factory=dict)
    target_command: str = ""
    target_view_path: list[str] = Field(default_factory=list)
    pre_commands: list[str] = Field(default_factory=list)
    negative_command: str | None = None
    reasoning: str | None = None
    sources: list[str] = Field(default_factory=list)
    confidence: str = "low"


@dataclass
class CandidateValidation:
    """自动校验结果。"""

    passed: bool
    errors: list[str] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)
    rendered_target: str | None = None
    captured: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "checks": self.checks,
            "rendered_target": self.rendered_target,
            "captured": self.captured,
        }


def is_sensitive(text: str) -> bool:
    """含密码、密钥、团体名的命令不落库、不送 LLM。"""
    lowered = text.lower()
    return any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)


def normalize_command_template(text: str) -> str:
    """把命令中的 IP 与数字抽象为占位符，作为缺口聚合键。"""
    tokens: list[str] = []
    for token in text.split():
        if _IPV4_RE.fullmatch(token):
            tokens.append("{ip}")
            continue
        tokens.append(_DIGITS_RE.sub("{num}", token))
    return " ".join(tokens)


def render_template(template: str, params: dict[str, str]) -> str:
    """用参数替换模板占位符，缺失时保留原样以便校验发现。"""

    def replace(matched: re.Match[str]) -> str:
        return params.get(matched.group(1), matched.group(0))

    return PLACEHOLDER_RE.sub(replace, template)


def allowed_views(
    registry: KnowledgeRegistry, vendor: str, device_type: str
) -> set[str]:
    """目标厂商允许的视图名集合，用于视图白名单校验。"""
    views = {"system-view"}
    for spec in registry.entities.values():
        views.update(_view_name(item) for item in spec.view_path)
    for impl in registry.implementations_for(vendor, device_type):
        if impl.view:
            views.add(_view_name(impl.view))
        views.update(_view_name(item) for item in impl.view_path)
    return views


def validate_candidate(
    payload: CandidatePayload,
    raw_sample: str,
    *,
    registry: KnowledgeRegistry,
    source_vendor: str,
    source_device_type: str,
    target_vendor: str,
    target_device_type: str,
) -> CandidateValidation:
    """按 4.7 的校验项逐条验证候选。"""
    errors: list[str] = []
    checks: dict[str, str] = {}

    if payload.status != "found":
        errors.append("模型未给出可用命令（status=unknown）")
        checks["status"] = "failed"
    else:
        checks["status"] = "passed"

    before = len(errors)
    if not payload.source_template.strip():
        errors.append("source_template 不能为空")
    if not payload.target_command.strip():
        errors.append("target_command 不能为空")
    checks["structure"] = "failed" if len(errors) > before else "passed"

    before = len(errors)
    if is_sensitive(payload.source_template) or is_sensitive(payload.target_command):
        errors.append("命令包含敏感关键字，不允许沉淀")
    checks["sensitive"] = "failed" if len(errors) > before else "passed"

    before = len(errors)
    parameters = _build_parameters(payload.parameters, errors)
    checks["parameters"] = "failed" if len(errors) > before else "passed"

    placeholders = extract_placeholders(payload.source_template) | extract_placeholders(
        payload.target_command
    )
    for template in payload.target_view_path:
        placeholders |= extract_placeholders(template)
    for template in payload.source_view_path:
        placeholders |= extract_placeholders(template)
    if payload.negative_command:
        placeholders |= extract_placeholders(payload.negative_command)
    for template in payload.pre_commands:
        placeholders |= extract_placeholders(template)
    undeclared = placeholders - set(parameters)
    if undeclared:
        errors.append(f"占位符未在参数表中声明：{sorted(undeclared)}")
        checks["placeholder"] = "failed"
    else:
        checks["placeholder"] = "passed"

    captured: dict[str, str] = {}
    if payload.source_template:
        try:
            compiled = compile_template(payload.source_template, parameters)
        except (ValueError, re.error) as exc:
            errors.append(f"源模板无法编译：{exc}")
        else:
            matched = compiled.match(raw_sample.strip())
            if matched is None:
                errors.append("源模板无法完整匹配原始命令（参数化不忠实）")
                checks["source_replay"] = "failed"
            else:
                captured = matched
                checks["source_replay"] = "passed"
    else:
        checks["source_replay"] = "failed"

    rendered_target = None
    if payload.target_command:
        rendered = render_template(payload.target_command, captured)
        if PLACEHOLDER_RE.search(rendered):
            errors.append("目标命令渲染后仍残留占位符")
            checks["render"] = "failed"
        else:
            rendered_target = rendered
            checks["render"] = "passed"
        if payload.negative_command:
            rendered_negative = render_template(payload.negative_command, captured)
            if PLACEHOLDER_RE.search(rendered_negative):
                errors.append("否定命令渲染后仍残留占位符")
                checks["render"] = "failed"

    if payload.target_view_path:
        target_views = allowed_views(registry, target_vendor, target_device_type)
        unknown = [
            item
            for item in payload.target_view_path
            if _view_name(item) not in target_views
        ]
        if unknown:
            errors.append(f"目标视图不在厂商视图白名单内：{unknown}")
            checks["target_view"] = "failed"
        else:
            checks["target_view"] = "passed"
    else:
        checks["target_view"] = "passed"

    if payload.source_view_path:
        source_views = allowed_views(registry, source_vendor, source_device_type)
        unknown = [
            item for item in payload.source_view_path if _view_name(item) not in source_views
        ]
        if unknown:
            errors.append(f"源视图不在厂商视图白名单内：{unknown}")
            checks["source_view"] = "failed"
        else:
            checks["source_view"] = "passed"

    return CandidateValidation(
        passed=not errors,
        errors=errors,
        checks=checks,
        rendered_target=rendered_target,
        captured=captured,
    )


def _build_parameters(
    raw: dict[str, CandidateParameter], errors: list[str]
) -> dict[str, ParameterSpec]:
    """把候选参数转换为知识库参数模型，非法枚举值记为校验失败。"""
    parameters: dict[str, ParameterSpec] = {}
    for name, item in raw.items():
        try:
            parameter_type = ParameterType(item.type)
        except ValueError:
            errors.append(f"参数 {name} 的 type 非法：{item.type}")
            continue
        value_format = None
        if item.format:
            try:
                value_format = ValueFormat(item.format)
            except ValueError:
                errors.append(f"参数 {name} 的 format 非法：{item.format}")
                continue
        try:
            parameters[name] = ParameterSpec(
                type=parameter_type,
                format=value_format,
                required=item.required,
                pattern=item.pattern,
                note=item.note,
            )
        except ValueError as exc:
            errors.append(f"参数 {name} 定义非法：{exc}")
    return parameters


def _view_name(template: str) -> str:
    return template.split(maxsplit=1)[0].lower()
