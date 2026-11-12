"""路由聚合：新增业务路由后在此注册。"""

from fastapi import APIRouter

from app.api import devices, health, translations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(devices.router)
api_router.include_router(translations.router)
