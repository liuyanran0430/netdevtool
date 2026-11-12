"""金样例：跨厂商配置翻译的精确输出。"""

from pathlib import Path

from app.translate_rule import translate_config
from app.translate_rule.registry import KnowledgeRegistry

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledges"
REGISTRY = KnowledgeRegistry.load(KNOWLEDGE_DIR)

SOURCE = """system-view
interface 10GE1/0/1
port link-type access
port default vlan 10
quit
ip route-static 192.168.5.0 255.255.255.0 192.168.4.2
"""


def test_golden_huawei_to_h3c() -> None:
    output = translate_config(
        SOURCE,
        source_vendor="huawei",
        source_device_type="switch",
        target_vendor="h3c",
        target_device_type="switch",
        registry=REGISTRY,
    )

    assert [(line.no, line.text, line.tone) for line in output.lines] == [
        (4, "system-view", "success"),
        (4, "  interface 10GE1/0/1", "success"),
        (4, "  port link-type access", "success"),
        (4, "  port access vlan 10", "warn"),
        (6, "  quit", "success"),
        (6, "  ip route-static 192.168.5.0 255.255.255.0 192.168.4.2", "success"),
        (6, "return", "success"),
    ]
    assert output.summary["translated"] == 2
    assert output.summary["unsupported"] == 0


def test_golden_huawei_to_zte() -> None:
    output = translate_config(
        SOURCE,
        source_vendor="huawei",
        source_device_type="switch",
        target_vendor="zte",
        target_device_type="switch",
        registry=REGISTRY,
    )

    assert [(line.no, line.text, line.tone) for line in output.lines] == [
        (4, "system-view", "success"),
        (4, "  interface 10GE1/0/1", "success"),
        (4, "  switchport mode access", "success"),
        (4, "  switchport access vlan 10", "warn"),
        (6, "  quit", "success"),
        (6, "  ip route 192.168.5.0 255.255.255.0 192.168.4.2", "warn"),
        (6, "return", "success"),
    ]
    assert output.summary["translated"] == 2
