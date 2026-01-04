from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import CmpBase
from .is_released_mixin import IsReleasedMixin

class CloudVendor(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cloud_vendors"
    __table_args__ = {"comment": "云厂商表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    cloud_code = Column(String(32), comment="云厂商code")
    cloud_name=Column(String(50), comment="云厂商名称")
    description = Column(Text, nullable=True, comment="描述")
    created_by = Column(Integer, nullable=False, comment="创建人")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )
