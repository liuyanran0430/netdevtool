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
    InterfaceNaming,
    ParameterSpec,
    SupplementEntry,
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
    interfaces: dict[tuple[str, str], dict[str, str]] = field(default_factory=dict)
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
    implementations, profiles, interfaces, skipped, warnings = _load_implementations(
        root, vendors_dir, result.entities
    )
    _load_supplements(root, result.entities, implementations, skipped, warnings)
    result.implementations = implementations
    result.profiles = profiles
    result.interfaces = interfaces
    result.skipped = skipped
    result.warnings = warnings

    logger.info(
        "知识库加载完成：entities=%d implementations=%d profiles=%d interfaces=%d skipped=%d warnings=%d",
        len(result.entities),
        len(result.implementations),
        len(result.profiles),
        len(result.interfaces),
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
    dict[tuple[str, str], dict[str, str]],
    list[str],
    list[str],
]:
    implementations: dict[tuple[str, str, str], Implementation] = {}
    profiles: dict[tuple[str, str], VendorProfile] = {}
    interfaces: dict[tuple[str, str], dict[str, str]] = {}
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
                    elif path.name == "_interfaces.yaml":
                        naming = _load_interfaces(path, rel, vendor, device_type, skipped)
                        if naming is not None:
                            interfaces[(vendor, device_type)] = naming.interfaces
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

    return implementations, profiles, interfaces, skipped, warnings


def _load_interfaces(
    path: Path,
    rel: str,
    vendor: str,
    device_type: str,
    errors: list[str],
) -> InterfaceNaming | None:
    """加载厂商接口命名规则，目录名优先于文件内声明。"""
    raw = _read_yaml(path, rel, errors)
    if raw is None:
        return None
    if not isinstance(raw, dict):
        errors.append(f"{rel}: 内容必须是对象")
        return None
    raw["vendor"] = vendor
    raw["device_type"] = device_type
    try:
        return InterfaceNaming.model_validate(raw)
    except ValidationError as exc:
        errors.append(f"{rel}: {_format_validation_error(exc)}")
        return None


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


def _load_supplements(
    root: Path,
    entities: dict[str, EntitySpec],
    implementations: dict[tuple[str, str, str], Implementation],
    skipped: list[str],
    warnings: list[str],
) -> None:
    """加载补充知识库，核心层永远优先。

    两种布局：
    - `supplements/{source_vendor}/{device_type}/{slug}.yaml`：合成 `ext_*` 实体
    - `supplements/impls/{target_vendor}/{device_type}/{entity_id}.yaml`：仅为既有实体补充实现
    """
    supplements_dir = root / "supplements"
    if not supplements_dir.is_dir():
        return

    for vendor_dir in sorted(path for path in supplements_dir.iterdir() if path.is_dir()):
        if vendor_dir.name.lower() == "impls":
            _load_supplement_impls(root, vendor_dir, entities, implementations, skipped, warnings)
            continue
        source_vendor = vendor_dir.name.lower()
        for type_dir in sorted(path for path in vendor_dir.iterdir() if path.is_dir()):
            device_type = type_dir.name.lower()
            for path in sorted(type_dir.glob("*.yaml")):
                rel = path.relative_to(root).as_posix()
                raw = _read_yaml(path, rel, skipped)
                if raw is None:
                    continue
                if not isinstance(raw, dict):
                    skipped.append(f"{rel}: 内容必须是对象")
                    continue
                try:
                    entry = SupplementEntry.model_validate(raw)
                except ValidationError as exc:
                    skipped.append(f"{rel}: {_format_validation_error(exc)}")
                    continue
                _register_supplement_entry(
                    entry, source_vendor, device_type, entities, implementations, skipped
                )


def _register_supplement_entry(
    entry: SupplementEntry,
    source_vendor: str,
    device_type: str,
    entities: dict[str, EntitySpec],
    implementations: dict[tuple[str, str, str], Implementation],
    skipped: list[str],
) -> None:
    entity_id = entry.id
    if entity_id in entities:
        skipped.append(f"supplements: 实体 {entity_id} 已存在于核心层，忽略补充条目")
        return

    source = entry.source
    parameters: dict[str, ParameterSpec] = dict(source.parameters)
    missing = extract_placeholders(source.command)
    for template in source.view_path:
        missing |= extract_placeholders(template)
    missing -= set(parameters)
    if missing:
        skipped.append(f"supplements: {entity_id} 使用了未定义参数 {sorted(missing)}")
        return

    entities[entity_id] = EntitySpec(
        id=entity_id,
        description=f"补充知识库：{source.command}",
        parameters=parameters,
    )
    source_impl = Implementation(
        entity_id=entity_id,
        vendor=source.vendor,
        device_type=source.device_type,
        product=source.product,
        os=source.os,
        supported=True,
        confidence="medium",
        command=source.command,
        view=_view_name(source.view_path),
        view_path=list(source.view_path),
        verified=True,
        origin="supplement",
    )
    implementations.setdefault((source_vendor, device_type, entity_id), source_impl)

    target = entry.target
    target_impl = Implementation(
        entity_id=entity_id,
        vendor=target.vendor,
        device_type=target.device_type,
        product=target.product,
        os=target.os,
        supported=True,
        confidence="medium",
        command=target.command,
        view=_view_name(target.view_path),
        view_path=list(target.view_path),
        pre_commands=list(target.pre_commands),
        negative_command=target.negative_command,
        verified=True,
        origin="supplement",
    )
    implementations.setdefault(
        (target.vendor.strip().lower(), target.device_type.strip().lower(), entity_id),
        target_impl,
    )


def _load_supplement_impls(
    root: Path,
    impls_dir: Path,
    entities: dict[str, EntitySpec],
    implementations: dict[tuple[str, str, str], Implementation],
    skipped: list[str],
    warnings: list[str],
) -> None:
    """加载 `supplements/impls` 下的实现补充，命中核心层时忽略。"""
    allowed_fields = set(Implementation.model_fields)
    for vendor_dir in sorted(path for path in impls_dir.iterdir() if path.is_dir()):
        vendor = vendor_dir.name.lower()
        for type_dir in sorted(path for path in vendor_dir.iterdir() if path.is_dir()):
            device_type = type_dir.name.lower()
            for path in sorted(type_dir.glob("*.yaml")):
                rel = path.relative_to(root).as_posix()
                raw = _read_yaml(path, rel, skipped)
                if raw is None:
                    continue
                if not isinstance(raw, dict):
                    skipped.append(f"{rel}: 内容必须是对象")
                    continue
                entity_id = str(raw.pop("extends", path.stem)).strip()
                if entity_id not in entities:
                    skipped.append(f"{rel}: 实体 {entity_id} 未在 entities 中定义")
                    continue
                key = (vendor, device_type, entity_id)
                if key in implementations:
                    warnings.append(f"{rel}: 核心层已有实现，忽略补充实现")
                    continue
                payload = {name: value for name, value in raw.items() if name in allowed_fields}
                payload.update(
                    entity_id=entity_id,
                    vendor=vendor,
                    device_type=device_type,
                    origin="supplement",
                )
                try:
                    implementations[key] = Implementation.model_validate(payload)
                except ValidationError as exc:
                    skipped.append(f"{rel}: {_format_validation_error(exc)}")


def _view_name(view_path: list[str]) -> str | None:
    """取视图路径最后一层作为命令所在视图类型。"""
    if not view_path:
        return None
    return view_path[-1].split(maxsplit=1)[0].lower()


def _missing_parameters(impl: Implementation, spec: EntitySpec) -> set[str]:
    used: set[str] = set()
    if impl.command:
        used |= extract_placeholders(impl.command)
    if impl.negative_command:
        used |= extract_placeholders(impl.negative_command)
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
