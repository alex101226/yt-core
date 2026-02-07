# app/core/init_app.py
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app import controllers

from app.core.config import settings
from app.core.logger import logger

from app.common.exceptions import (
BusinessException,
business_exception_handler,
global_exception_handler,
validation_exception_handler
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前逻辑
    logger.info("🚀 Application starting up...")
    from app.tasks.settle_billing_task import bill_start_scheduler, bill_stop_scheduler
    bill_start_scheduler()
    try:
        yield
    finally:
        bill_stop_scheduler()
        logger.info("🛑 Application shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Yuetai Core",
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    # origins = ["http://127.0.0.1:3004", "http://127.0.0.1:3005"]
    # ✅ 跨域配置
    app.add_middleware(
        CORSMiddleware,
        # allow_origins=origins,
        allow_origins=["*"],  # 允许所有来源前端调用（开发阶段可先用 *）
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有请求方法：GET/POST/PUT/DELETE
        allow_headers=["*"],  # 允许所有自定义头
    )

    # include routers
    routers = [getattr(controllers, name) for name in controllers.__routes__]
    for r in routers:
        app.include_router(r, prefix=settings.API_PREFIX)

    # 注册全局异常处理
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # ⭐ 必须加
    app.add_exception_handler(Exception, global_exception_handler)

    return app

