"""设备查询路由。"""

import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import DeviceType, User
from app.schemas import DeviceManualOut, DeviceOut
from app.services.device_service import (
    DeviceNotFound,
    ManualNotFound,
    list_devices,
    resolve_manual,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceOut], summary="查询设备列表")
def get_devices(
    vendor: str | None = Query(None, description="设备厂商，精确匹配"),
    device_type: DeviceType | None = Query(
        None, description="设备类型：switch=交换机，firewall=防火墙"
    ),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[DeviceOut]:
    return list_devices(db, vendor=vendor, device_type=device_type)


@router.get("/manual", response_model=None, summary="打开设备手册")
def get_device_manual(
    vendor: str = Query(..., description="设备厂商"),
    model: str = Query(..., description="设备型号"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DeviceManualOut | FileResponse:
    """外部链接返回 JSON，本地文件直接以 inline 方式返回文件流。"""
    try:
        kind, target = resolve_manual(db, vendor=vendor, model=model)
    except DeviceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ManualNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if kind == "external":
        return DeviceManualOut(kind="external", url=str(target))

    path = target
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, content_disposition_type="inline")
