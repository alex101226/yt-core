# 负载均衡实例
# id
# name
# cloud_provider
# cloud_credential_id
# region
# vpc_id
# subnet_id
# network_type          # 公网 / 私网
# instance_type         # 共享 / 独享
# spec                  # 实例规格
# bandwidth
# billing_type
# service_address       # EIP 或私网 IP
# status                # CREATING / RUNNING / ERROR
# tags
# description
# created_by
# created_at
# updated_at

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Enum as SAEnum, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin
from ...constants.enums import BillingMethod, LoadBalancerStatus, NetworkType, LBInstanceType


class LoadBalancer(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_instance"
    __table_args__ = {'comment': '负载均实例'}


    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    lb_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="云厂商负载均衡实例ID")
    lb_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="负载均衡实例名称")

    resource_group_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="云厂商编码")
    region_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="区域ID")

    vpc_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="所属VPC ID")
    subnet_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="所属子网ID")

    network_type: Mapped[NetworkType] = mapped_column(
        SAEnum(NetworkType), nullable=False, comment="网络类型：公网/私网"
    )

    instance_type: Mapped[LBInstanceType] = mapped_column(
        SAEnum(LBInstanceType), nullable=False, comment="实例类型：按规格/按用量"
    )

    instance_model: Mapped[str] = mapped_column(
        String(64), nullable=True, comment="实例型号，如 lb.small, lb.medium"
    )

    bandwidth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="带宽上限(Mbps)")

    charge_type: Mapped[BillingMethod] = mapped_column(
        SAEnum(BillingMethod), nullable=False, comment="计费方式：按量/包年包月"
    )
    private_ip: Mapped[str] = mapped_column(String(128), nullable=True, comment="私网的ip")
    public_ip: Mapped[str] = mapped_column(String(128), nullable=True, comment="公网的ip，自动分配")

    status: Mapped[LoadBalancerStatus] = mapped_column(
        SAEnum(LoadBalancerStatus), nullable=False, comment="负载均衡实例状态"
    )

    # 元数据
    tags: Mapped[JSON] = mapped_column(JSON, nullable=True, comment="标签")
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="描述信息")
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="创建用户ID")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )
