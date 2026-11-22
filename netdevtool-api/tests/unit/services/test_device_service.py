"""设备服务：厂商名归一与手册外链、本地路径安全约束。"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.models import Device
from app.repositories.device_repository import DeviceRepository
from app.services import device_service


def device(manual_path: str | None = None) -> Device:
    return Device(
        id=1,
        vendor="华为",
        vendor_en="huawei",
        model="S5735",
        manual_path=manual_path,
    )


def test_normalize_vendor_accepts_chinese_key_and_passthrough_values(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        DeviceRepository, "find_by_vendor", lambda self, value: device()
    )

    assert device_service.normalize_vendor(db, "华为") == "huawei"
    assert device_service.normalize_vendor(db, " all ") == "all"
    assert device_service.normalize_vendor(db, "  ") is None


def test_normalize_unknown_vendor_uses_lowercase_key(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(DeviceRepository, "find_by_vendor", lambda self, value: None)

    assert device_service.normalize_vendor(db, " Unknown-Vendor ") == "unknown-vendor"


def test_resolve_manual_returns_external_url_without_touching_filesystem(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: device("https://docs.example.com/S5735.pdf"),
    )

    assert device_service.resolve_manual(db, vendor="华为", model="S5735") == (
        "external",
        "https://docs.example.com/S5735.pdf",
    )


def test_resolve_manual_finds_file_under_docs_directory(
    db: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "knowledges"
    manual = root / "docs" / "S5735.pdf"
    manual.parent.mkdir(parents=True)
    manual.write_bytes(b"manual")
    monkeypatch.setattr(device_service, "default_knowledge_dir", lambda: root)
    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: device("S5735.pdf"),
    )

    kind, path = device_service.resolve_manual(db, vendor="华为", model="S5735")

    assert kind == "local"
    assert path == manual.resolve()


def test_resolve_manual_rejects_path_traversal_outside_knowledge_root(
    db: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "knowledges"
    root.mkdir()
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"secret")
    monkeypatch.setattr(device_service, "default_knowledge_dir", lambda: root)
    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: device("../outside.pdf"),
    )

    with pytest.raises(device_service.ManualNotFound):
        device_service.resolve_manual(db, vendor="华为", model="S5735")


def test_resolve_manual_distinguishes_missing_device_and_manual(
    db: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: None,
    )
    with pytest.raises(device_service.DeviceNotFound):
        device_service.resolve_manual(db, vendor="华为", model="missing")

    monkeypatch.setattr(
        DeviceRepository,
        "find_by_vendor_and_model",
        lambda self, vendor, model: device(None),
    )
    with pytest.raises(device_service.ManualNotFound, match="未配置手册"):
        device_service.resolve_manual(db, vendor="华为", model="S5735")
