"""设备服务：查询流程编排。"""

from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Device, DeviceType
from app.repositories.device_repository import DeviceRepository
from app.translate_rule.loader import default_knowledge_dir


class DeviceNotFound(Exception):
    """设备档案不存在。"""


class ManualNotFound(Exception):
    """设备未配置手册或手册文件不存在。"""


def list_devices(
    db: Session,
    *,
    vendor: str | None,
    device_type: DeviceType | None,
) -> list[Device]:
    return DeviceRepository(db).list_devices(vendor=vendor, device_type=device_type)


def normalize_vendor(db: Session, vendor: str | None) -> str | None:
    """把厂商名归一为设备档案中的英文 key，供知识库 payload 比对。

    接受中文名（华为/中兴）或已是英文 key（huawei/zte）；`all`、空值原样返回。
    """
    value = (vendor or "").strip()
    if not value or value.lower() == "all":
        return value or None

    device = DeviceRepository(db).find_by_vendor(value)
    if device is None:
        return value.lower()
    return (device.vendor_en or device.vendor).strip().lower()


def resolve_manual(db: Session, *, vendor: str, model: str) -> tuple[str, str | Path]:
    """解析设备手册：返回 ("external", 链接) 或 ("local", 知识库下的文件路径)。"""
    device = DeviceRepository(db).find_by_vendor_and_model(vendor, model)
    if device is None:
        raise DeviceNotFound(f"设备档案不存在：{vendor} {model}")

    raw = (device.manual_path or "").strip()
    if not raw:
        raise ManualNotFound(f"{vendor} {model} 未配置手册")

    if raw.lower().startswith(("http://", "https://")):
        return "external", raw

    root = default_knowledge_dir().resolve()
    # 兼容只写文件名（实际放在 knowledges/docs 下）与写全相对路径两种填法
    for candidate in (root / raw, root / "docs" / raw):
        path = candidate.resolve()
        # 只允许读取知识库目录内的文件，避免路径穿越
        if path.is_relative_to(root) and path.is_file():
            return "local", path
    raise ManualNotFound(f"手册文件不存在：{raw}")
