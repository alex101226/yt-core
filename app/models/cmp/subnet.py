# app/models/cmp/subnet.py
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Boolean
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings

class Subnet(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}subnet"
    __table_args__ = (
        UniqueConstraint("cloud_provider_code", "subnet_id", name="uq_provider_subnetid"),
        {"comment": "云厂商子网信息表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    subnet_id = Column(String(50), nullable=False, comment="云厂商原始子网ID，例如 vsw-xxxx/subnet-xxx")
    subnet_name = Column(String(100), nullable=False, comment="子网名称")
    description = Column(Text, nullable=True, comment="子网描述信息")

    # VPC、资源组、云厂商、云凭证
    vpc_id = Column(String(50), nullable=False, comment="所属VPC ID")
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    cloud_certificate_id = Column(Integer, nullable=False, comment="云凭证ID")

    # 区域、可用区
    region_id = Column(String(100), nullable=False, comment="区域ID")
    zone_id = Column(String(50), nullable=True, comment="可用区ID")

    # 子网网段
    cidr_block = Column(String(50), nullable=False, comment="子网网段，例如 192.168.1.0/24")

    # 释放字段
    is_released = Column(Boolean, default=False, nullable=False, comment="是否已释放")
    released_at = Column(DateTime(timezone=True), nullable=True, comment="释放时间 (UTC)")

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
