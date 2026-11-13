"""应用入口。

OpenAPI 契约：/openapi.json（Swagger UI: /docs，ReDoc: /redoc）
修改接口后执行 script/export_openapi.py 刷新契约文件，前端类型以其为准手工同步。
"""

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.config import settings
from app.schemas import ErrorResponse

TAGS_METADATA = [
    {"name": "system", "description": "系统与健康检查"},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="NetDevTool 后端接口，前后端以 OpenAPI 契约为准。",
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = ErrorResponse(code=exc.status_code, message=str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=jsonable_encoder(body))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        body = ErrorResponse(code=422, message="请求参数校验失败", detail=exc.errors())
        return JSONResponse(status_code=422, content=jsonable_encoder(body))

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
