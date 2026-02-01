from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import SsoBase
from app.core.config import settings
from app.models.is_released_mixin import SSOReleasedMixin

class Role(SsoBase, SSOReleasedMixin):
    __tablename__ = f"{settings.SSO_TABLE_PREFIX}roles"
    __table_args__ = {"comment": "角色表"}   # 表注释

    id = Column(Integer, primary_key=True, comment="角色ID")
    role_code=Column(String(50), unique=True, comment="角色编号")
    role_name = Column(String(50), nullable=False, comment="角色名称")
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
