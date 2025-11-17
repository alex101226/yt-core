# app/core/init_app.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.common.exceptions import BusinessException, business_exception_handler, global_exception_handler
from app.core.config import settings
from app.core.logger import logger

from app.controllers import (
cloud_provider_router,
cloud_region_router,
cloud_zone_router,
cloud_certificate_router,
resource_group_router,
resource_group_binding_router,
dict_router,
vpc_router,
subnet_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前逻辑
    logger.info("🚀 Application starting up...")
    yield
    # 关闭时逻辑
    logger.info("🛑 Application shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Yuetai Core",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # ✅ 跨域配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源前端调用（开发阶段可先用 *）
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有请求方法：GET/POST/PUT/DELETE
        allow_headers=["*"],  # 允许所有自定义头
    )

    # include routers
    routers = [
        cloud_provider_router,
        cloud_region_router,
        cloud_zone_router,
        cloud_certificate_router,
        resource_group_router,
        resource_group_binding_router,
        dict_router,
        vpc_router,
        subnet_router
    ]
    for r in routers:
        app.include_router(r, prefix=settings.API_PREFIX)

    # 注册全局异常处理
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    return app

