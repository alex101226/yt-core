from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin


class QuotaCategory(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}quota_category"
    __table_args__ = {"comment": "付费配额类别表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    resource_type = Column(String(32), nullable=False, unique=True, comment="资源类型编码")
    quota_name = Column(String(64), nullable=False, comment="配额类别名称")
    quota_code = Column(String(64), nullable=False, unique=True, comment="配额编码")
    quantity_type = Column(String(32), nullable=False, comment="数量类型")
    description = Column(String(255), nullable=True, comment="描述")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间(UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间(UTC)",
    )
