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

# 统一取 token
def get_token_from_request(request: Request) -> Optional[str]:
    # 1. 优先从 Cookie 取
    token = request.cookies.get("access_token")
    if token:
        return token

    # 2. 兜底从 Authorization 取（兼容旧逻辑）
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth[7:]

    return None


"""
内部复用函数：尝试解码 access token。
- 成功返回 payload(dict)
- token 不存在返回 None
- token 无效或不是 access 类型抛 BusinessException
"""
def decode_access_token(token: Optional[str]) -> Optional[Dict]:
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

def get_current_user(request: Request) -> Dict:
    token = get_token_from_request(request)
    payload = decode_access_token(token)

    if payload is None:
        raise BusinessException(
            code=ErrorCode.UNAUTHORIZED,
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

