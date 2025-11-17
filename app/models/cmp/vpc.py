# app/models/cmp/vpc.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings

class Vpc(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}vpc"
    __table_args__ = {"comment": "云厂商虚拟私有网络（VPC）信息表"}

    id = Column(String(50), primary_key=True)
    vpc_name = Column(String(100), nullable=False, comment="VPC 名称")
    description = Column(Text, nullable=True, comment="VPC 描述信息")

    # 资源组、云厂商、云凭证
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code = Column(Integer, nullable=False, comment="云厂商code")
    cloud_certificate_id = Column(Integer, nullable=False, comment="云凭证ID")

    # 区域
    region_id = Column(String(100), nullable=False, comment="区域ID")

    # 网络类型
    network_type = Column(String(20), nullable=False, comment="网络类型，例如 VPC/CLASSIC")

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
