# app/core/dependencies.py
from typing import Optional, Dict

from fastapi import Request, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger
from app.core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_bearer_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth[7:]

"""
内部复用函数：尝试解码 access token。
- 成功返回 payload(dict)
- token 不存在返回 None
- token 无效或不是 access 类型抛 BusinessException
"""
def _decode_access_token_or_none(token: Optional[str]) -> Optional[Dict]:
    if not token:
        return None

    try:
        payload = decode_token(token)
    except Exception:
        # token 无效或过期
        raise BusinessException(
            code=ErrorCode.INVALID_OR_EXPIRED_TOKEN,
            message=Message.INVALID_TOKEN
        )

    # 确保是 access token
    if payload.get("type") != "access":
        raise BusinessException(
            code=ErrorCode.INVALID_TOKEN_TYPE,
            message=Message.INVALID_TOKEN_TYPE if hasattr(Message, "INVALID_TOKEN_TYPE") else "Access token required"
        )

    return payload

"""
可选依赖：没有 token 返回 None；有 token 返回 payload（并在无效时抛 BusinessException）。
适用场景：登录可选的接口（浏览、投票等）。
"""
def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
):
    token = credentials.credentials if credentials else None
    return _decode_access_token_or_none(token)

"""
强制依赖：必须有 token（否则抛 BusinessException），并返回 payload。
适用场景：必须登录才可访问的接口（/me、/logout、修改资料等）。
"""
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> Dict:
    token = credentials.credentials if credentials else None
    payload = _decode_access_token_or_none(token)

    if payload is None:
        # 明确区分未提供 token（未登录）与无效 token（decode 已抛异常）
        raise BusinessException(
            code=ErrorCode.PERMISSION_DENIED if hasattr(ErrorCode, "PERMISSION_DENIED") else ErrorCode.UNAUTHORIZED,
            message=Message.UNAUTHORIZED
        )

    return payload


def require_user(request: Request, user = Depends(get_current_user)):
    if not user:
        raise BusinessException(
            code=ErrorCode.UNAUTHORIZED,
            message="Not authenticated"
        )
    request.state.user = user
    return user

