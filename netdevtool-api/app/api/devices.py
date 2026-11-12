"""设备查询路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DeviceType
from app.schemas import DeviceOut
from app.services.device_service import list_device_types, list_devices

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("/types", response_model=list[DeviceType], summary="查询设备类型枚举")
def get_device_types(db: Session = Depends(get_db)) -> list[DeviceType]:
    return list_device_types(db)


@router.get("", response_model=list[DeviceOut], summary="查询设备列表")
def get_devices(
    vendor: str | None = Query(None, description="设备厂商，精确匹配"),
    device_type: DeviceType | None = Query(
        None, description="设备类型：switch=交换机，firewall=防火墙"
    ),
    db: Session = Depends(get_db),
) -> list[DeviceOut]:
    return list_devices(db, vendor=vendor, device_type=device_type)
