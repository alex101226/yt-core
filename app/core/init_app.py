# app/core/init_app.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# from app.core.cache import get_redis
from app.core.config import settings
from app.core.logger import logger

from app.common.exceptions import (
BusinessException,
business_exception_handler,
global_exception_handler,
validation_exception_handler
)

from app.controllers import (
dict_router,
auth_router,
user_router,
user_certificate_router,
resource_group_router,
cloud_router,
vpc_router,
subnet_router,
security_group_router,
server_instance_router,
bare_metal_instance_router,
eip_router,
cbs_router,
oss_router,
gpfs_router,
cephfs_file_router,
fs_mount_router,
container_image_router,
cluster_router,
account_router,
# image_router,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前逻辑
    logger.info("🚀 Application starting up...")
    from app.tasks.server_instance_status_checker import start_scheduler, stop_scheduler

    # start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()
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
        dict_router,
        auth_router,
        user_router,
        account_router,
        user_certificate_router,
        resource_group_router,
        cloud_router,
        vpc_router,
        subnet_router,
        security_group_router,
        server_instance_router,
        bare_metal_instance_router,
        eip_router,
        cbs_router,
        oss_router,
        gpfs_router,
        cephfs_file_router,
        fs_mount_router,
        container_image_router,
        cluster_router,
        # image_router,
    ]
    for r in routers:
        app.include_router(r, prefix=settings.API_PREFIX)

    # 注册全局异常处理
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # ⭐ 必须加
    app.add_exception_handler(Exception, global_exception_handler)

    return app

