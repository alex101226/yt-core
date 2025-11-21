from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import SsoBase
from app.core.config import settings
from app.models.sso.user_role_association import user_role_association

class Role(SsoBase):
    __tablename__ = f"{settings.SSO_TABLE_PREFIX}roles"
    __table_args__ = {"comment": "角色表"}   # 表注释

    id = Column(Integer, primary_key=True, comment="角色ID")
    role_name = Column(String(50), unique=True, index=True, comment="角色名称")
    description = Column(String(200), nullable=True, comment="角色描述")

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
    users = relationship(
        "User",
        secondary=user_role_association,  # 中间表
        back_populates="roles"
    )
