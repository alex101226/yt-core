from datetime import datetime, timezone

from sqlalchemy import Column, Integer, Table, ForeignKey, DateTime
from app.core.database import SsoBase
from app.core.config import settings

user_role_association = Table(
    f"{settings.SSO_TABLE_PREFIX}user_roles",
    SsoBase.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey(f"{settings.SSO_TABLE_PREFIX}users.id", name="fk_user_roles_user_id"),
        primary_key=True
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey(f"{settings.SSO_TABLE_PREFIX}roles.id", name="fk_user_roles_role_id"),
        primary_key=True
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        default=datetime.now(timezone.utc)
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc)
    ),
    comment="用户角色关联表"
)
