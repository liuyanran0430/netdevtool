"""设备服务：查询流程编排。"""

from sqlalchemy.orm import Session

from app.models import Device, DeviceType
from app.repositories.device_repository import DeviceRepository


def list_devices(
    db: Session,
    *,
    vendor: str | None,
    device_type: DeviceType | None,
) -> list[Device]:
    return DeviceRepository(db).list_devices(vendor=vendor, device_type=device_type)
