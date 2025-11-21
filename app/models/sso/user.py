from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import SsoBase
from app.core.config import settings
from app.models.sso.user_role_association import user_role_association

class User(SsoBase):
    __tablename__ = f"{settings.SSO_TABLE_PREFIX}users"
    __table_args__ = {"comment": "用户表"}  # 表注释

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    username = Column(String(50), unique=True, index=True, comment="登录用户名")
    hashed_password = Column(String(200), comment="加密后的密码")
    email = Column(String(100), nullable=True, comment="邮箱")
    nickname = Column(String(50), nullable=True, comment="昵称")
    mobile = Column(String(20), nullable=True, comment="手机号码")

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

    roles = relationship(
        "Role",
        secondary=user_role_association,  # 中间表
        back_populates="users"
    )
