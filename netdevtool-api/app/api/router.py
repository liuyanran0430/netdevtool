"""路由聚合：新增业务路由后在此注册。"""

from fastapi import APIRouter

from app.api import auth, chat, devices, health, knowledge, review, translations

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(devices.router)
api_router.include_router(translations.router)
api_router.include_router(knowledge.router)
api_router.include_router(review.router)
api_router.include_router(chat.router)
