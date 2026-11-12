"""健康检查路由（前端联调冒烟用）。"""

from fastapi import APIRouter

from app.config import settings
from app.schemas import APIModel

router = APIRouter(tags=["system"])


class HealthResponse(APIModel):
    status: str
    env: str


@router.get("/health", response_model=HealthResponse, summary="健康检查")
def health() -> HealthResponse:
    return HealthResponse(status="ok", env=settings.APP_ENV)
