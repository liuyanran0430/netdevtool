"""知识库驱动的配置翻译：加载、解析、渲染的纯单元入口。

当前不接入 Celery 与数据库，供规则验证与单元测试使用。
"""

import time
from pathlib import Path

from app.translate_rule.loader import KnowledgeLoadError, LoadResult, load_knowledge
from app.translate_rule.models import (
    EntitySpec,
    Implementation,
    ParameterSpec,
    ParameterType,
    ValueFormat,
    VendorProfile,
)
from app.translate_rule.parser import ParsedEntity, ParsedLine, SourceParser
from app.translate_rule.registry import (
    KnowledgeRegistry,
    get_registry,
    reload_registry,
)
from app.translate_rule.renderer import (
    RenderWarning,
    RenderedLine,
    Renderer,
    TranslationOutput,
)

__all__ = [
    "EntitySpec",
    "Implementation",
    "KnowledgeLoadError",
    "KnowledgeRegistry",
    "LoadResult",
    "ParameterSpec",
    "ParameterType",
    "ParsedEntity",
    "ParsedLine",
    "RenderWarning",
    "RenderedLine",
    "Renderer",
    "SourceParser",
    "TranslationOutput",
    "ValueFormat",
    "VendorProfile",
    "get_registry",
    "load_knowledge",
    "reload_registry",
    "translate_config",
]


def translate_config(
    source_text: str,
    *,
    source_vendor: str,
    source_device_type: str,
    target_vendor: str,
    target_device_type: str,
    registry: KnowledgeRegistry | None = None,
) -> TranslationOutput:
    """按知识库把源配置翻译为目标厂商配置。"""
    active_registry = registry or get_registry()
    started = time.perf_counter()
    parsed_lines = SourceParser(active_registry, source_vendor, source_device_type).parse(source_text)
    duration_ms = int((time.perf_counter() - started) * 1000)
    renderer = Renderer(
        active_registry,
        target_vendor,
        target_device_type,
        source_vendor=source_vendor,
        source_device_type=source_device_type,
    )
    return renderer.render(parsed_lines, duration_ms=duration_ms)
