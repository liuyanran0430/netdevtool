"""设备仓储：数据库读写唯一入口。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Device, DeviceType


class DeviceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_devices(
        self,
        *,
        vendor: str | None = None,
        device_type: DeviceType | None = None,
    ) -> list[Device]:
        """按条件查询设备列表。"""
        stmt = select(Device)

        if vendor:
            stmt = stmt.where(Device.vendor == vendor)
        if device_type is not None:
            stmt = stmt.where(Device.device_type == device_type)

        return list(self.db.scalars(stmt.order_by(Device.id)))

    def find_by_vendor_and_model(self, vendor: str, model: str) -> Device | None:
        """按厂商与型号精确查询设备档案。"""
        stmt = select(Device).where(Device.vendor == vendor, Device.model == model)
        return self.db.scalars(stmt).first()
