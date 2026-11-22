"""Golden Cases：真实规则知识库驱动的核心配置转换。"""

from pathlib import Path

import pytest

from app.translate_rule import KnowledgeRegistry, translate_config

KNOWLEDGE_ROOT = Path(__file__).resolve().parents[4] / "knowledges"


@pytest.fixture(scope="module")
def registry() -> KnowledgeRegistry:
    return KnowledgeRegistry.load(KNOWLEDGE_ROOT)


def translate(registry: KnowledgeRegistry, source: str, target: str = "h3c"):
    return translate_config(
        source,
        source_vendor="huawei",
        source_device_type="switch",
        target_vendor=target,
        target_device_type="switch",
        registry=registry,
    )


def compact_lines(output) -> list[str]:
    return [line.text.strip() for line in output.lines]


def test_static_route_golden_case(registry: KnowledgeRegistry) -> None:
    output = translate(
        registry, "ip route-static 10.0.0.0 255.255.255.0 192.168.1.1"
    )

    assert compact_lines(output) == [
        "system-view",
        "ip route-static 10.0.0.0 255.255.255.0 192.168.1.1",
        "return",
    ]
    assert output.summary["translated"] == 1
    assert output.summary["unsupported"] == 0


def test_interface_command_maps_interface_name_and_marks_review(
    registry: KnowledgeRegistry,
) -> None:
    output = translate(
        registry,
        "interface 10GE1/0/1\n description uplink-to-core\n quit",
    )

    assert compact_lines(output) == [
        "system-view",
        "interface XGE1/0/1",
        "description uplink-to-core",
        "quit",
        "return",
    ]
    assert "intf_translated" in {warning.code for warning in output.warnings}
    assert output.lines[1].tone == "warn"
    assert output.lines[2].text.strip() == "description uplink-to-core"


def test_negative_command_uses_target_vendor_specific_form(
    registry: KnowledgeRegistry,
) -> None:
    output = translate(
        registry, "interface GE0/0/1\n undo portswitch\n quit"
    )

    assert "port link-mode route" in compact_lines(output)
    assert "undo portswitch" not in compact_lines(output)
    assert output.summary["translated"] == 1


def test_unknown_command_is_preserved_with_error_warning(
    registry: KnowledgeRegistry,
) -> None:
    output = translate(registry, "some-vendor-specific action 42")

    assert compact_lines(output) == [
        "system-view",
        "some-vendor-specific action 42",
        "return",
    ]
    assert output.lines[1].tone == "error"
    assert output.warnings[0].code == "unknown_command"
    assert output.summary["unsupported"] == 1
