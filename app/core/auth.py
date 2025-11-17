# app/core/auth.py
from typing import Optional
from sqlalchemy.orm import Session

def verify_token(token: str, db: Optional[Session] = None) -> Optional[dict]:
    """
    简单示例：把 token == "fake-token" 视为有效并返回一个 user dict。
    在真实项目中，你需要：
      - 校验 token 的签名 / 到期 / 黑名单
      - 根据 token 查 sso_auth 数据库获取用户
      - 返回用户对象或 None
    """
    if not token:
        return None

    # === 占位逻辑 ===
    if token == "fake-token":
        return {"id": 1, "username": "admin", "roles": ["admin"]}
    return None
