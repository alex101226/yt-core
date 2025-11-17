# app/common/response.py
from typing import Any, Generic
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic.v1.fields import T
from pydantic.v1.generics import GenericModel

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

class ResponseModel(GenericModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T


def _orm_to_dict(obj: Any) -> dict:
    """把 SQLAlchemy ORM 实例转成纯 Python dict（只取非私有属性）。"""
    try:
        return {k: v for k, v in getattr(obj, "__dict__", {}).items() if not k.startswith("_")}
    except Exception:
        return {"repr": str(obj)}

def _convert_payload(data: Any):
    """
    1) 把 Pydantic BaseModel 转成 dict
    2) 把 ORM 实例转成 dict
    3) 对 list/tuple 做逐项处理
    4) 最后用 jsonable_encoder 做全面的可序列化转换（datetime -> isoformat 等）
    """
    if data is None:
        return None

    # Pydantic model
    if isinstance(data, BaseModel):
        raw = data.model_dump()
        return jsonable_encoder(raw)

    # list / tuple
    if isinstance(data, (list, tuple)):
        items = []
        for d in data:
            if isinstance(d, BaseModel):
                items.append(d.model_dump())
            elif hasattr(d, "__dict__"):
                items.append(_orm_to_dict(d))
            else:
                items.append(d)
        return jsonable_encoder(items)

    # ORM instance (has __dict__)
    if hasattr(data, "__dict__"):
        raw = _orm_to_dict(data)
        return jsonable_encoder(raw)

    # already plain types (dict/int/str/etc.)
    return jsonable_encoder(data)


class Response:
    @staticmethod
    def success(data: Any = None, message: str = Message.SUCCESS):
        payload = _convert_payload(data)
        return JSONResponse(
            status_code=200,
            content={
                "code": ErrorCode.SUCCESS,
                "message": message,
                "data": payload,
            },
        )

    @staticmethod
    def fail(message: str = Message.FAILED, code: int = ErrorCode.FAILED):
        raise BusinessException(code=code, message=message)
