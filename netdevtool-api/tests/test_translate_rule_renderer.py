"""命令渲染单元测试。"""

from pathlib import Path

from app.translate_rule.parser import ParsedEntity, ParsedLine, SourceParser
from app.translate_rule.registry import KnowledgeRegistry
from app.translate_rule.renderer import Renderer

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledges"
REGISTRY = KnowledgeRegistry.load(KNOWLEDGE_DIR)

SOURCE = """system-view
interface 10GE1/0/1
port link-type access
port default vlan 10
"""


def _render(source: str, target_vendor: str, target_device_type: str = "switch"):
    parsed = SourceParser(REGISTRY, "huawei", "switch").parse(source)
    renderer = Renderer(
        REGISTRY,
        target_vendor,
        target_device_type,
        source_vendor="huawei",
        source_device_type="switch",
    )
    return renderer.render(parsed)


def test_render_huawei_to_h3c() -> None:
    output = _render(SOURCE, "h3c")

    texts = [line.text for line in output.lines]
    assert texts == [
        "system-view",
        "  interface 10GE1/0/1",
        "  port link-type access",
        "  port access vlan 10",
        "  quit",
        "return",
    ]
    assert output.summary["translated"] == 1
    assert output.summary["unsupported"] == 0
    assert any("接口名" in warning.message for warning in output.warnings)
    assert next(line for line in output.lines if line.text == "  port access vlan 10").tone == "warn"


def test_render_unsupported_target_device_type() -> None:
    output = _render(SOURCE, "dptech")

    assert output.lines[0].text == "# 目标设备不支持: port_access_vlan"
    assert output.lines[0].tone == "warn"
    assert output.summary["unsupported"] == 1


def test_render_parameter_out_of_range() -> None:
    source = """system-view
interface 10GE1/0/1
port link-type access
port default vlan 5000
"""

    output = _render(source, "h3c")

    assert "参数校验失败" in output.lines[0].text
    assert "超出范围" in output.lines[0].text
    assert output.summary["unsupported"] == 1


def test_render_supported_false(tmp_path: Path) -> None:
    (tmp_path / "entities").mkdir()
    (tmp_path / "entities" / "demo.yaml").write_text(
        "id: demo\nview_path: [\"system-view\"]\nparameters:\n  name:\n    type: string\n    required: true\n",
        encoding="utf-8",
    )
    target_dir = tmp_path / "vendors" / "acme" / "switch"
    target_dir.mkdir(parents=True)
    (target_dir / "demo.yaml").write_text(
        "entity_id: demo\nvendor: acme\ndevice_type: switch\nsupported: false\n"
        "unsupported_reason: 该设备不支持\n",
        encoding="utf-8",
    )
    registry = KnowledgeRegistry.load(tmp_path)

    parsed = [ParsedLine(1, "demo test", "command", ParsedEntity("demo", {"name": "test"}, "system-view"))]
    renderer = Renderer(registry, "acme", "switch", source_vendor="huawei", source_device_type="switch")
    output = renderer.render(parsed)

    assert output.lines[0].text == "# 目标设备不支持: demo"
    assert output.summary["unsupported"] == 1


def test_render_inserts_exit_between_sibling_interfaces() -> None:
    source = """system-view
interface 10GE1/0/1
port default vlan 10
interface 10GE1/0/2
port default vlan 20
"""
    output = _render(source, "h3c")

    texts = [line.text for line in output.lines]
    assert texts.count("  quit") == 2
    assert texts.index("  quit") < texts.index("  interface 10GE1/0/2")
    assert texts[-1] == "return"


def test_profile_allows_direct_view_switch(tmp_path: Path) -> None:
    (tmp_path / "entities").mkdir()
    (tmp_path / "entities" / "demo.yaml").write_text(
        'id: demo\nview_path: ["system-view", "interface {intf}"]\n'
        "parameters:\n  intf:\n    type: string\n    required: true\n",
        encoding="utf-8",
    )
    vendor_dir = tmp_path / "vendors" / "acme" / "switch"
    vendor_dir.mkdir(parents=True)
    (vendor_dir / "demo.yaml").write_text(
        "entity_id: demo\nvendor: acme\ndevice_type: switch\n"
        'command: "demo {intf}"\nview: interface\n',
        encoding="utf-8",
    )
    (vendor_dir / "_profile.yaml").write_text(
        "vendor: acme\ndevice_type: switch\n"
        "allow_direct_view_switch: true\nauto_close_views: false\n",
        encoding="utf-8",
    )
    registry = KnowledgeRegistry.load(tmp_path)

    parsed = [
        ParsedLine(1, "system-view", "view"),
        ParsedLine(2, "interface a", "view"),
        ParsedLine(3, "demo a", "command", ParsedEntity("demo", {"intf": "a"}, "interface")),
        ParsedLine(4, "demo b", "command", ParsedEntity("demo", {"intf": "b"}, "interface")),
    ]
    output = Renderer(registry, "acme", "switch").render(parsed)

    assert [line.text for line in output.lines] == [
        "system-view",
        "  interface a",
        "  demo a",
        "  interface b",
        "  demo b",
    ]


def test_render_meta_and_duration() -> None:
    output = _render(SOURCE, "h3c")

    assert output.meta["source"] == {"vendor": "huawei", "device_type": "switch"}
    assert output.meta["target"] == {"vendor": "h3c", "device_type": "switch"}
    assert output.meta["entities_used"] == ["port_access_vlan"]
    assert output.summary["total"] == len(output.lines)
