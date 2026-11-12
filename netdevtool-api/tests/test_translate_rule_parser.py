"""源配置解析单元测试。"""

from pathlib import Path

from app.translate_rule.parser import SourceParser
from app.translate_rule.registry import KnowledgeRegistry

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledges"
REGISTRY = KnowledgeRegistry.load(KNOWLEDGE_DIR)

HUAWEI_SOURCE = """system-view
interface 10GE1/0/1
port link-type access
port default vlan 10
quit
ip route-static 192.168.5.0 255.255.255.0 192.168.4.2
"""


def test_parse_huawei_access_and_static_route() -> None:
    parsed = SourceParser(REGISTRY, "huawei", "switch").parse(HUAWEI_SOURCE)

    assert [line.kind for line in parsed] == [
        "view",
        "view",
        "pre",
        "command",
        "view",
        "command",
    ]
    access = parsed[3].entity
    assert access is not None
    assert access.entity_id == "port_access_vlan"
    assert access.params == {"intf": "10GE1/0/1", "vlan_id": "10"}

    route = parsed[5].entity
    assert route is not None
    assert route.entity_id == "static_route"
    assert route.params == {
        "prefix": "192.168.5.0",
        "mask": "255.255.255.0",
        "next_hop": "192.168.4.2",
    }


def test_parse_huawei_trunk_vlan_list() -> None:
    source = """system-view
interface 10GE1/0/2
port link-type trunk
port trunk allow-pass vlan 10 20
"""

    parsed = SourceParser(REGISTRY, "huawei", "switch").parse(source)

    entity = parsed[3].entity
    assert entity is not None
    assert entity.entity_id == "port_trunk_vlan"
    assert entity.params["vlan_list"] == "10 20"
    assert entity.params["intf"] == "10GE1/0/2"


def test_parse_zte_switchport_style() -> None:
    source = """system-view
interface gei_1/1
switchport mode access
switchport access vlan 20
"""

    parsed = SourceParser(REGISTRY, "zte", "switch").parse(source)

    entity = parsed[3].entity
    assert entity is not None
    assert entity.entity_id == "port_access_vlan"
    assert entity.params == {"intf": "gei_1/1", "vlan_id": "20"}


def test_comment_blank_and_unmatched_lines() -> None:
    source = """# 注释

port default vlan 10
"""

    parsed = SourceParser(REGISTRY, "huawei", "switch").parse(source)

    assert [line.kind for line in parsed] == ["comment", "blank", "other"]
    assert parsed[2].entity is None


def test_interface_view_replaced_by_next_interface() -> None:
    source = """system-view
interface 10GE1/0/1
port link-type access
port default vlan 10
interface 10GE1/0/2
port default vlan 20
"""

    parsed = SourceParser(REGISTRY, "huawei", "switch").parse(source)

    first = parsed[3].entity
    second = parsed[5].entity
    assert first is not None and first.params["intf"] == "10GE1/0/1"
    assert second is not None and second.params["intf"] == "10GE1/0/2"
