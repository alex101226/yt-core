# app/models/cmp/network_vpc.py
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings

from app.models.is_released_mixin import IsReleasedMixin

class Vpc(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}vpc"
    __table_args__ = (UniqueConstraint("cloud_provider_code", "vpc_id", name="uq_provider_vpcid"),
                      {"comment": "云厂商虚拟私有网络（VPC）信息表"},)

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_by = Column(Integer, index=True, nullable=False, comment="属于哪个用户")

    # 云资源 ID（AWS: vpc-xxx, 阿里云: vpc-xxxx），自己创建的会自动生成12位随机值
    vpc_id = Column(String(50), nullable=True, comment="云厂商返回的 VPC ID")

    # 基本信息
    vpc_name = Column(String(100), nullable=False, comment="VPC 名称")
    description = Column(Text, nullable=True, comment="VPC 描述信息")

    # 资源组、云厂商、云凭证
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    # cloud_certificate_id = Column(Integer, nullable=False, comment="云凭证ID")

    # 区域
    region_id = Column(String(100), nullable=False, comment="区域ID")

    # 网络类型
    network_type = Column(String(20), nullable=False, comment="网络类型，例如 VPC/CLASSIC")
    service_cidr = Column(String(64), nullable=False, comment="网段")

    # 被使用次数
    used_count = Column(Integer, default=0, comment="被使用次数")

    status = Column(String(50), default="AVAILABLE", comment="vpc的状态，字典表type_code=VPC_STATUS")
    sync_status = Column(
        Integer,
        default=0,
        comment="同步状态：0未同步，1已同步，2待更新，3删除中"
    )

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
