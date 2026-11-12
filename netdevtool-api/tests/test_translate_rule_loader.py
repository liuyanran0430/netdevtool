"""知识库加载与索引单元测试。"""

from pathlib import Path

import pytest

from app.translate_rule.loader import KnowledgeLoadError, load_knowledge
from app.translate_rule.registry import KnowledgeRegistry

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledges"

ENTITY_YAML = """
id: demo
view_path: ["system-view"]
parameters:
  name:
    type: string
    required: true
"""

IMPLEMENTATION_YAML = """
entity_id: demo
vendor: acme
device_type: switch
command: "demo {name}"
view: system-view
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_base(root: Path, *, device_type: str = "switch", filename: str = "demo.yaml") -> None:
    _write(root / "entities" / "demo.yaml", ENTITY_YAML)
    _write(root / "vendors" / "acme" / device_type / filename, IMPLEMENTATION_YAML)


def test_load_real_knowledge_base() -> None:
    result = load_knowledge(KNOWLEDGE_DIR)

    assert set(result.entities) == {"port_access_vlan", "port_trunk_vlan", "static_route"}
    assert len(result.implementations) == 9
    assert len(result.profiles) == 3
    assert result.profiles[("huawei", "switch")].view_exit == "quit"
    assert result.skipped == []


def test_registry_resolve_normalizes_case() -> None:
    registry = KnowledgeRegistry.load(KNOWLEDGE_DIR)

    implementation = registry.resolve("Huawei", "SWITCH", "port_access_vlan")

    assert implementation is not None
    assert implementation.command == "port default vlan {vlan_id}"


def test_registry_common_fallback(tmp_path: Path) -> None:
    _write(tmp_path / "entities" / "demo.yaml", ENTITY_YAML)
    _write(tmp_path / "vendors" / "acme" / "common" / "demo.yaml", IMPLEMENTATION_YAML)

    registry = KnowledgeRegistry.load(tmp_path)

    assert registry.resolve("acme", "switch", "demo") is not None
    assert registry.resolve("acme", "firewall", "demo") is not None


def test_unknown_entity_is_skipped(tmp_path: Path) -> None:
    _write(tmp_path / "entities" / "demo.yaml", ENTITY_YAML)
    _write(
        tmp_path / "vendors" / "acme" / "switch" / "ghost.yaml",
        "entity_id: ghost\nvendor: acme\ndevice_type: switch\ncommand: \"ghost\"\n",
    )

    result = load_knowledge(tmp_path)

    assert result.implementations == {}
    assert any("ghost" in message for message in result.skipped)


def test_duplicate_implementation_is_skipped(tmp_path: Path) -> None:
    _build_base(tmp_path)
    _write(tmp_path / "vendors" / "acme" / "switch" / "demo_copy.yaml", IMPLEMENTATION_YAML)

    result = load_knowledge(tmp_path)

    assert len(result.implementations) == 1
    assert any("实现重复" in message for message in result.skipped)


def test_device_type_mismatch_uses_directory(tmp_path: Path) -> None:
    _build_base(tmp_path / "kb")
    _write(tmp_path / "kb" / "vendors" / "acme" / "firewall" / "demo.yaml", IMPLEMENTATION_YAML)

    result = load_knowledge(tmp_path / "kb")

    assert any("device_type" in message for message in result.warnings)
    assert ("acme", "firewall", "demo") in result.implementations


def test_duplicate_entity_raises(tmp_path: Path) -> None:
    _write(tmp_path / "entities" / "a.yaml", ENTITY_YAML)
    _write(tmp_path / "entities" / "b.yaml", ENTITY_YAML)
    _write(tmp_path / "vendors" / "acme" / "switch" / "demo.yaml", IMPLEMENTATION_YAML)

    with pytest.raises(KnowledgeLoadError):
        load_knowledge(tmp_path)
