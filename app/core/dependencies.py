# app/core/dependencies.py
from fastapi import Depends, HTTPException, Request
from app.core.security import decode_token
from app.core.config import settings

def get_bearer_token(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth[7:]

def get_current_user_optional(token: str = Depends(get_bearer_token)):
    if not token:
        return None
    try:
        payload = decode_token(token)
        # 只允许 access token here
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        return {"user_id": payload.get("user_id"), "username": payload.get("username")}
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
