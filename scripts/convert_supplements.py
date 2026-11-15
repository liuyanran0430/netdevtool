"""补充规则转换脚本：supplements -> entities + vendors。

把 knowledges/supplements/{vendor}/{device_type}/*.yaml 里的 AI 补充规则
改写成核心知识库结构：
- knowledges/entities/{entity_id}.yaml
- knowledges/vendors/{source_vendor}/{device_type}/{entity_id}.yaml
- knowledges/vendors/{target_vendor}/{device_type}/{entity_id}.yaml

用法（在项目根目录执行，使用后端虚拟环境的 Python）：
    python scripts/convert_supplements.py --dry-run       # 只预览，不落盘
    python scripts/convert_supplements.py                 # 写入，已存在的文件跳过
    python scripts/convert_supplements.py --force         # 覆盖已存在的实体/实现
    python scripts/convert_supplements.py --delete-source # 转换成功后删除补充 YAML

约定：
- entity_id 由补充 id 去掉 ext_ 前缀、目标厂商后缀和参数占位符后缀得到，
  例如 ext_stp_mode_mode_zte_switch -> stp_mode
- 已存在的实体不覆盖，仅补齐缺失的厂商实现（--force 时全部覆盖）
- 生成的实体/实现会用 app.translate_rule.models 校验，校验失败不写文件
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledges"
SUPPLEMENT_DIR = KNOWLEDGE_DIR / "supplements"
ENTITY_DIR = KNOWLEDGE_DIR / "entities"
VENDOR_DIR = KNOWLEDGE_DIR / "vendors"
API_DIR = ROOT / "netdevtool-api"

# 复用后端契约模型做校验，避免生成 schema 不接受的 YAML
sys.path.insert(0, str(API_DIR))
from app.translate_rule.models import EntitySpec, Implementation  # noqa: E402


def clean(value: Any) -> Any:
    """去掉空值，并把元组转为列表，保证 PyYAML 可安全序列化。"""
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items() if item is not None and item != []}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    return value


def dump_yaml(path: Path, payload: dict[str, Any]) -> str:
    text = yaml.safe_dump(
        clean(payload),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=1000,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return text


def split_product_os(product: str | None) -> tuple[str | None, str | None]:
    """补充规则把型号与版本写在 product 里（型号/版本），拆开后与核心实现一致。"""
    if not product:
        return None, None
    if "/" not in product:
        return product, None
    model, os_version = product.rsplit("/", 1)
    return model.strip() or None, os_version.strip() or None


def view_name(view_path: list[str]) -> str | None:
    """与 loader._view_name 保持一致：取视图路径最后一层的首个单词。"""
    if not view_path:
        return None
    return view_path[-1].split(maxsplit=1)[0].lower()


def derive_entity_id(entry: dict[str, Any]) -> str:
    """从补充 id 推导实体 id，去掉 ext_ 前缀、目标后缀与参数占位符后缀。"""
    source = entry.get("source") or {}
    target = entry.get("target") or {}
    raw = str(entry.get("id") or "").strip()
    if raw.startswith("ext_"):
        raw = raw[4:]

    suffix = f"_{target.get('vendor', '')}_{target.get('device_type', '')}".lower()
    if suffix != "_" and raw.lower().endswith(suffix):
        raw = raw[: -len(suffix)]

    params = sorted((source.get("parameters") or {}), key=len, reverse=True)
    for name in params:
        tail = f"_{name}"
        if raw.endswith(tail) and len(raw) > len(tail):
            raw = raw[: -len(tail)]

    raw = re.sub(r"[^0-9a-zA-Z]+", "_", raw).strip("_").lower()
    if raw:
        return raw

    # 兜底：用源命令里的固定关键字拼实体 id（去掉占位符）
    command = re.sub(r"\{[^}]*\}", " ", str(source.get("command") or ""))
    tokens = [token.lower() for token in re.findall(r"[A-Za-z0-9]+", command)]
    return "_".join(tokens) or "supplement"


def build_entity(entity_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    source = entry["source"]
    target = entry["target"]
    notes = [f"由补充规则 {entry['id']} 转换"]
    notes.append(
        f"目标实现：{target['vendor']}/{target['device_type']} {target['command']}"
    )
    for case in entry.get("cases") or []:
        notes.append(f"用例：{case['source']} -> {case['target']}")

    return {
        "id": entity_id,
        "description": f"补充知识库：{source['command']}",
        "view_path": list(source.get("view_path") or []),
        "parameters": source.get("parameters") or {},
        "semantic_notes": notes,
    }


def build_impl(entity_id: str, entry: dict[str, Any], side: str) -> dict[str, Any]:
    data = entry[side]
    view_path = list(data.get("view_path") or [])
    product, os_version = split_product_os(data.get("product"))
    payload: dict[str, Any] = {
        "entity_id": entity_id,
        "vendor": data["vendor"],
        "device_type": data["device_type"],
        "product": product,
        "os": os_version or data.get("os"),
        "supported": True,
        "confidence": "medium",
        "command": data["command"],
        "view": view_name(view_path),
        "view_path": view_path,
        "verified": bool(entry.get("verified")) or bool(entry.get("accepted_by")),
        "sources": list(entry.get("sources") or []),
    }
    if side == "target":
        payload["pre_commands"] = list(data.get("pre_commands") or [])
        payload["negative_command"] = data.get("negative_command")
    return payload


def validate(entity: dict[str, Any], impls: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    try:
        EntitySpec.model_validate(entity)
    except Exception as exc:  # noqa: BLE001 - 校验信息直接回显给用户
        errors.append(f"实体校验失败：{exc}")
    for impl in impls:
        try:
            Implementation.model_validate(impl)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"实现校验失败（{impl['vendor']}）：{exc}")
    return errors


def collect_supplements() -> list[tuple[Path, dict[str, Any]]]:
    entries: list[tuple[Path, dict[str, Any]]] = []
    if not SUPPLEMENT_DIR.is_dir():
        return entries
    for path in sorted(SUPPLEMENT_DIR.rglob("*.yaml")):
        relative = path.relative_to(SUPPLEMENT_DIR).parts
        # supplements/impls 是“仅补充实现”的专用目录，不参与实体转换
        if not relative or relative[0] == "impls" or len(relative) != 3:
            continue
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict) or "source" not in raw or "target" not in raw:
            print(f"[跳过] {path}: 不是补充规则格式")
            continue
        entries.append((path, raw))
    return entries


def convert(path: Path, entry: dict[str, Any], force: bool, delete_source: bool) -> None:
    entity_id = derive_entity_id(entry)
    entity = build_entity(entity_id, entry)
    source_impl = build_impl(entity_id, entry, "source")
    target_impl = build_impl(entity_id, entry, "target")

    errors = validate(entity, [source_impl, target_impl])
    if errors:
        print(f"[失败] {path.name}:")
        for error in errors:
            print(f"  - {error}")
        return

    entity_path = ENTITY_DIR / f"{entity_id}.yaml"
    impl_paths = [
        VENDOR_DIR / source_impl["vendor"] / source_impl["device_type"] / f"{entity_id}.yaml",
        VENDOR_DIR / target_impl["vendor"] / target_impl["device_type"] / f"{entity_id}.yaml",
    ]

    print(f"\n{path.name} -> entity_id={entity_id}")
    if entity_path.exists() and not force:
        print(f"  [跳过] 实体已存在：{entity_path.relative_to(ROOT)}")
    else:
        dump_yaml(entity_path, entity)
        print(f"  [写入] {entity_path.relative_to(ROOT)}")

    for impl_path, impl in zip(impl_paths, [source_impl, target_impl]):
        if impl_path.exists() and not force:
            print(f"  [跳过] 实现已存在：{impl_path.relative_to(ROOT)}")
            continue
        dump_yaml(impl_path, impl)
        print(f"  [写入] {impl_path.relative_to(ROOT)}")

    if delete_source:
        all_ready = entity_path.exists() and all(item.exists() for item in impl_paths)
        if all_ready:
            path.unlink()
            print(f"  [删除] 原补充规则 {path.relative_to(ROOT)}")
        else:
            print("  [保留] 仍有文件未生成，不删除原补充规则")


def main() -> None:
    parser = argparse.ArgumentParser(description="把 supplements 补充规则转换为 entities + vendors YAML")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要写入的内容，不落盘")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的实体/实现文件")
    parser.add_argument("--delete-source", action="store_true", help="转换成功后删除原补充规则")
    args = parser.parse_args()

    entries = collect_supplements()
    if not entries:
        print("未找到需要转换的补充规则")
        return

    if args.dry_run:
        for path, entry in entries:
            entity_id = derive_entity_id(entry)
            print(f"\n=== {path.name} -> {entity_id} ===")
            print("--- entity ---")
            print(yaml.safe_dump(clean(build_entity(entity_id, entry)), allow_unicode=True, sort_keys=False))
            for side in ("source", "target"):
                print(f"--- {side} impl ---")
                print(yaml.safe_dump(clean(build_impl(entity_id, entry, side)), allow_unicode=True, sort_keys=False))
        return

    for path, entry in entries:
        convert(path, entry, force=args.force, delete_source=args.delete_source)

    print("\n完成。修改知识库后需重启 Celery Worker（以及后端）才会加载新文件。")


if __name__ == "__main__":
    main()
