# app/models/cmp/network_eip.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

from app.models.is_released_mixin import IsReleasedMixin


class Eip(CmpBase, IsReleasedMixin):
    """
    弹性公网 IP (EIP) 资源表
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}network_eip"
    __table_args__ = {"comment": "弹性公网 IP 资源表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")

    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商")
    region_id = Column(String(50), nullable=False, comment="地域ID")
    zone_id = Column(String(50), nullable=True, comment="可用区ID")

    description = Column(Text, nullable=True, comment="描述")

    # 云端标识
    eip_id = Column(String(100), nullable=True, comment="EIP ID")
    eip_name = Column(String(100), nullable=True, comment="EIP 的名称")
    public_ip = Column(String(50), nullable=True, comment="分配的公网 IP")

    # 绑定信息
    bind_instance_id = Column(String(100), nullable=True, comment="绑定的实例ID")
    bind_instance_type = Column(String(50), nullable=True, comment="绑定实例类型，如 ecs/bms/lb")
    bind_private_ip = Column(String(50), nullable=True, comment="绑定实例内网IP")

    # 计费信息
    internet_charge_type = Column(String(30), nullable=False, default="PayByBandwidth", comment="公网计费类型")
    bandwidth = Column(Integer, nullable=False, comment="带宽上限 Mbps")

    # 状态信息
    status = Column(String(50), default="ALLOCATING", comment="EIP 状态")
    sync_status = Column(Integer, default=1, comment="同步状态：1待执行 2同步中 3成功 4失败")
    last_operation = Column(String(50), nullable=True, comment="最近一次操作：CREATE/BIND/UNBIND/RELEASE")
    error_message = Column(Text, nullable=True, comment="失败原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )
