# models/hub_categories.py
from sqlalchemy import Column, BigInteger, String, DateTime
from datetime import datetime, timezone
from app.core.database import HubBase
from app.core.config import settings


class HubCategories(HubBase):
    __tablename__ = f"{settings.HUB_TABLE_PREFIX}categories"
    __table_args__ = {"comment": "模型分类表"}

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )

    name = Column(
        String(64),
        nullable=False,
        comment="分类名称"
    )

    slug = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="唯一标识"
    )

    description = Column(
        String(255),
        nullable=True,
        comment="分类描述"
    )

    icon = Column(
        String(64),
        nullable=True,
        comment="分类图标"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
