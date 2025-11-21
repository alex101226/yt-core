# app/models/sso/session.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.database import SsoBase
from app.core.config import settings

class UserSession(SsoBase):
    __tablename__ = f"{settings.SSO_TABLE_PREFIX}sessions"
    __table_args__ = {"comment": "用户登录会话（refresh token 存储）；用于单点登录"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(f"{settings.SSO_TABLE_PREFIX}users.id"), nullable=False, index=True, comment="用户ID")
    refresh_token = Column(String(512), nullable=False, comment="刷新 token（hash 或原文）")
    expires_at = Column(DateTime, nullable=False, comment="刷新 token 到期时间")
    ip = Column(String(64), nullable=True, comment="登录IP")
    user_agent = Column(String(512), nullable=True, comment="客户端 UA")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
