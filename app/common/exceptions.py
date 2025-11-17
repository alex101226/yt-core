# app/common/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger


class BusinessException(Exception):
    """业务层异常（统一格式）"""
    def __init__(self, code: int = ErrorCode.FAILED, message: str = Message.FAILED):
        self.code = code
        self.message = message

    def to_response(self):
        """返回标准响应"""
        return JSONResponse(
            status_code=400,
            content={
                "code": self.code,
                "message": self.message,
                "data": None
            }
        )


async def business_exception_handler(request: Request, exc: BusinessException):
    """全局捕获业务异常"""
    logger.warning(f"BusinessException: {exc.code} - {exc.message}")
    return exc.to_response()


async def global_exception_handler(request: Request, exc: Exception):
    """兜底捕获所有未处理异常"""
    logger.error(f"Unhandled Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": ErrorCode.SERVER_ERROR,
            "message": Message.SERVER_ERROR,
            "data": None
        }
    )
