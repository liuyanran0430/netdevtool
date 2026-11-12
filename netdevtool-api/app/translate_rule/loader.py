"""知识库加载：扫描目录、解析 YAML、校验并建立实现索引。"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from app.config import settings
from app.translate_rule.models import (
    EntitySpec,
    Implementation,
    VendorProfile,
    extract_placeholders,
)

logger = logging.getLogger(__name__)


class KnowledgeLoadError(RuntimeError):
    """知识库结构性错误，加载方应阻止应用启动。"""


@dataclass
class LoadResult:
    """一次加载的结果。"""

    base_dir: Path
    entities: dict[str, EntitySpec] = field(default_factory=dict)
    implementations: dict[tuple[str, str, str], Implementation] = field(default_factory=dict)
    profiles: dict[tuple[str, str], VendorProfile] = field(default_factory=dict)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def default_knowledge_dir() -> Path:
    """知识库根目录：优先取配置，缺省为项目根下的 knowledges。"""
    if settings.KNOWLEDGE_BASE_DIR:
        return Path(settings.KNOWLEDGE_BASE_DIR).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "knowledges"


def load_knowledge(base_dir: str | Path | None = None) -> LoadResult:
    """加载整个知识库。

    结构性错误（实体目录缺失、实体重复）直接抛 `KnowledgeLoadError`；
    单个厂商实现文件的问题记录到 `skipped`，不阻塞其余文件。
    """
    root = Path(base_dir).expanduser().resolve() if base_dir else default_knowledge_dir()
    entities_dir = root / "entities"
    vendors_dir = root / "vendors"
    if not entities_dir.is_dir():
        raise KnowledgeLoadError(f"实体目录不存在：{entities_dir}")
    if not vendors_dir.is_dir():
        raise KnowledgeLoadError(f"厂商目录不存在：{vendors_dir}")

    result = LoadResult(base_dir=root)
    result.entities = _load_entities(entities_dir)
    implementations, profiles, skipped, warnings = _load_implementations(
        root, vendors_dir, result.entities
    )
    result.implementations = implementations
    result.profiles = profiles
    result.skipped = skipped
    result.warnings = warnings

    logger.info(
        "知识库加载完成：entities=%d implementations=%d profiles=%d skipped=%d warnings=%d",
        len(result.entities),
        len(result.implementations),
        len(result.profiles),
        len(result.skipped),
        len(result.warnings),
    )
    for message in result.skipped:
        logger.warning("知识库跳过：%s", message)
    for message in result.warnings:
        logger.warning("知识库告警：%s", message)
    return result


def _load_entities(entities_dir: Path) -> dict[str, EntitySpec]:
    entities: dict[str, EntitySpec] = {}
    errors: list[str] = []
    for path in sorted(entities_dir.glob("*.yaml")):
        rel = path.name
        raw = _read_yaml(path, rel, errors)
        if raw is None:
            continue
        if not isinstance(raw, dict):
            errors.append(f"{rel}: 内容必须是对象")
            continue
        try:
            spec = EntitySpec.model_validate(raw)
        except ValidationError as exc:
            errors.append(f"{rel}: {_format_validation_error(exc)}")
            continue
        if spec.id in entities:
            errors.append(f"{rel}: 实体 {spec.id} 重复定义")
            continue
        missing = set()
        for template in spec.view_path:
            missing |= extract_placeholders(template) - set(spec.parameters)
        if missing:
            errors.append(f"{rel}: view_path 使用了未定义参数 {sorted(missing)}")
            continue
        entities[spec.id] = spec

    if errors:
        raise KnowledgeLoadError("实体加载失败：" + "；".join(errors))
    return entities


def _load_implementations(
    root: Path,
    vendors_dir: Path,
    entities: dict[str, EntitySpec],
) -> tuple[
    dict[tuple[str, str, str], Implementation],
    dict[tuple[str, str], VendorProfile],
    list[str],
    list[str],
]:
    implementations: dict[tuple[str, str, str], Implementation] = {}
    profiles: dict[tuple[str, str], VendorProfile] = {}
    skipped: list[str] = []
    warnings: list[str] = []

    for vendor_dir in sorted(path for path in vendors_dir.iterdir() if path.is_dir()):
        vendor = vendor_dir.name.lower()
        for type_dir in sorted(path for path in vendor_dir.iterdir() if path.is_dir()):
            device_type = type_dir.name.lower()
            for path in sorted(type_dir.glob("*.yaml")):
                rel = path.relative_to(root).as_posix()
                if path.stem.startswith("_"):
                    if path.name == "_profile.yaml":
                        profile = _load_profile(path, rel, vendor, device_type, skipped)
                        if profile is not None:
                            profiles[(vendor, device_type)] = profile
                    continue
                raw = _read_yaml(path, rel, skipped)
                if raw is None:
                    continue
                if not isinstance(raw, dict):
                    skipped.append(f"{rel}: 内容必须是对象")
                    continue

                declared_type = str(raw.get("device_type", "")).strip().lower()
                if not declared_type:
                    warnings.append(f"{rel}: 缺少 device_type，按目录推断为 {device_type}")
                elif declared_type != device_type:
                    warnings.append(
                        f"{rel}: device_type={declared_type} 与目录 {device_type} 不一致，以目录为准"
                    )
                raw["device_type"] = device_type

                declared_vendor = str(raw.get("vendor", "")).strip().lower()
                if declared_vendor and declared_vendor != vendor:
                    warnings.append(
                        f"{rel}: vendor={declared_vendor} 与目录 {vendor} 不一致，以目录为准"
                    )
                raw["vendor"] = vendor

                try:
                    impl = Implementation.model_validate(raw)
                except ValidationError as exc:
                    skipped.append(f"{rel}: {_format_validation_error(exc)}")
                    continue

                spec = entities.get(impl.entity_id)
                if spec is None:
                    skipped.append(f"{rel}: 实体 {impl.entity_id} 未在 entities 中定义")
                    continue

                missing = _missing_parameters(impl, spec)
                if missing:
                    skipped.append(f"{rel}: 使用了未定义参数 {sorted(missing)}")
                    continue

                key = (vendor, device_type, impl.entity_id)
                if key in implementations:
                    skipped.append(f"{rel}: 实现重复 {key}")
                    continue
                implementations[key] = impl

    return implementations, profiles, skipped, warnings


def _load_profile(
    path: Path,
    rel: str,
    vendor: str,
    device_type: str,
    errors: list[str],
) -> VendorProfile | None:
    """加载厂商级 profile，目录名优先于文件内声明。"""
    raw = _read_yaml(path, rel, errors)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        errors.append(f"{rel}: 内容必须是对象")
        return None
    raw["vendor"] = vendor
    raw["device_type"] = device_type
    try:
        return VendorProfile.model_validate(raw)
    except ValidationError as exc:
        errors.append(f"{rel}: {_format_validation_error(exc)}")
        return None


def _missing_parameters(impl: Implementation, spec: EntitySpec) -> set[str]:
    used: set[str] = set()
    if impl.command:
        used |= extract_placeholders(impl.command)
    for template in impl.pre_commands:
        used |= extract_placeholders(template)
    return used - set(spec.parameters)


def _read_yaml(path: Path, label: str, errors: list[str]) -> object | None:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001  YAML 解析错误需要原样记录
        errors.append(f"{label}: YAML 解析失败：{exc}")
        return None


def _format_validation_error(exc: ValidationError) -> str:
    parts = []
    for item in exc.errors():
        location = ".".join(str(part) for part in item["loc"])
        parts.append(f"{location}: {item['msg']}")
    return "；".join(parts)
