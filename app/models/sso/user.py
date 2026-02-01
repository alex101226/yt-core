from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import SsoBase
from app.core.config import settings
from app.models.is_released_mixin import SSOReleasedMixin

class User(SsoBase, SSOReleasedMixin):
    __tablename__ = f"{settings.SSO_TABLE_PREFIX}users"
    __table_args__ = {"comment": "用户表"}  # 表注释

    id = Column(Integer, primary_key=True, comment="主键ID")
    username = Column(String(50), unique=True, index=True, comment="登录用户名")
    hashed_password = Column(String(200), comment="加密后的密码")
    nickname = Column(String(50), nullable=True, comment="昵称")

    role_code = Column(
        String(50),
        ForeignKey(f"{settings.SSO_TABLE_PREFIX}roles.role_code"),
        nullable=True,
        index=True,
        comment="权限Code（角色标识）"
    )
    parent_id = Column(
        Integer,
        default=0,
        nullable=False,
        comment="上级用户ID"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间 (UTC)"
    )

    # 可选：角色关系映射
    role = relationship("Role", backref="users")
