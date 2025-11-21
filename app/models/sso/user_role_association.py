from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Table, ForeignKey, DateTime
from app.core.database import SsoBase
from app.core.config import settings

user_role_association = Table(
    f"{settings.SSO_TABLE_PREFIX}user_roles",
    SsoBase.metadata,
    Column("user_id", Integer, ForeignKey(f"{settings.SSO_TABLE_PREFIX}users.id")),
    Column("role_id", Integer, ForeignKey(f"{settings.SSO_TABLE_PREFIX}roles.id")),
    Column("created_at", DateTime, default=datetime.now(timezone.utc)),
    Column("updated_at", DateTime, onupdate=datetime.now(timezone.utc)),
    comment="用户角色关联表"
)
