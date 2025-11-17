# app/models/public/cloud_zone.py
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint

from app.core.config import settings
from app.core.database import PublicBase

class CloudZone(PublicBase):
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}cloud_zone"
    __table_args__ = (
        UniqueConstraint('provider_code', 'region_id', 'zone_id', name='uq_provider_region_zone'),
        {'comment': '云厂商可用区列表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_code = Column(String(50), nullable=False, comment='云厂商编码，例如 aliyun')
    region_id = Column(String(100), nullable=False, comment='所属区域的 region_id')
    zone_id = Column(String(100), nullable=False, comment='可用区代号，例如 cn-hangzhou-a')
    zone_name = Column(String(200), nullable=False, comment='可用区名称，例如 华东1可用区A')
    created_at = Column(DateTime, nullable=False, comment='创建时间 (UTC)')
    updated_at = Column(DateTime, nullable=False, comment='更新时间 (UTC)')
