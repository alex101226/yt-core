from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, UniqueConstraint
from app.core.config import settings
from app.core.database import PublicBase

class CloudRegion(PublicBase):
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}cloud_region"
    __table_args__ = (
    UniqueConstraint('provider_code', 'region_id', name='uq_provider_region'),
        {'comment': '云厂商区域列表'}
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_code = Column(String(50), nullable=False, comment="云厂商编码，例如 aliyun")
    region_id = Column(String(100), nullable=False, comment="地区代号（如 cn-hangzhou）")
    region_name = Column(String(200), nullable=False, comment="地区名称（如 华东1（杭州））")
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