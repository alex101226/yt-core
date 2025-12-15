from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

from .is_released_mixin import IsReleasedMixin

class BareMetalInstance(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}baremetal_instance"
    __table_args__ = {"comment": "裸金属实例表"}

    # ---------- 基础信息 ----------
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_name = Column(String(128), nullable=False, comment="实例名称")
    hostname = Column(String(128), nullable=True, comment="主机名")
    description = Column(Text, nullable=True, comment="描述")

    # ---------- 云 & 账号 ----------
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商")
    region_id = Column(String(64), nullable=False, comment="区域")
    zone_id = Column(String(64), nullable=True, comment="可用区")
    resource_group_id = Column(Integer, nullable=True, comment="资源组")

    # ---------- 规格 ----------
    instance_type = Column(String(20), nullable=True, comment="实例规格类型，例如：如 ebm/bm")
    instance_type_id = Column(String(100), nullable=False, comment="实例规格 ID，如 ecs.g6.large")
    cpu = Column(Integer, nullable=True, comment="CPU核数")
    gpu = Column(Integer, nullable=True, comment="GPU核数")
    system_disk_category = Column(String(50), nullable=False, comment="系统盘类型，例如 ESSD_PL0, SSD")
    system_disk_size = Column(Integer, nullable=True, comment="内存(MB)")

    # ---------- 操作系统 ----------
    image_id = Column(String(128), nullable=False, comment="系统镜像ID")
    os_type = Column(String(32), nullable=True, comment="操作系统类型")
    os_version = Column(String(64), nullable=True, comment="操作系统版本")

    # ---------- 网络 ----------
    vpc_id = Column(Integer, nullable=True, comment="VPC ID")
    vswitch_id = Column(Integer, nullable=True, comment="子网ID")
    private_ip = Column(String(64), nullable=True, comment="内网IP")
    public_ip = Column(String(64), nullable=True, comment="公网IP")
    internet_max_bandwidth_out = Column(Integer, nullable=True, comment="公网最大带宽（Mbps）")
    network_interfaces = Column(JSON, nullable=True, comment="网卡信息(JSON)")

    # ---------- 安全 ----------
    security_group_id = Column(String(100), nullable=True, comment="安全组 ID")
    hashed_password = Column(String(256), nullable=True, comment="管理员密码(加密)")
    key_pair_name = Column(String(100), nullable=True, comment="SSH 密钥名称（可选）")
    enable_ssh_agent = Column(Boolean, default=False, comment="是否开启 SSH 代理")
    ssh_proxy_port = Column(Integer, default=False, comment="SSH 代理端口")
    login_mode = Column(String(20), nullable=False, default="PASSWORD", comment="登录方式：PASSWORD / KEYPAIR")
    enable_protection = Column(Boolean, default=False, comment="是否开启释放保护")

    # ---------- 计费 ----------
    instance_charge_type = Column(
        String(10),
        nullable=False,
        comment="实例计费类型:PrePaid（包年包月）/PostPaid（按量付费）"
    )
    internet_charge_type = Column(String(30), nullable=True, comment="公网计费类型：PayByBandwidth/PayByTraffic")
    period = Column(Integer, nullable=True, comment="购买周期(月)")
    quantity = Column(Integer, default=1, comment="购买数量")
    auto_renew = Column(Boolean, default=False, comment="是否到期自动续费(仅包年包月)")

    # ---------- 裸金属特有 ----------
    instance_id = Column(String(128), nullable=True, comment="云侧裸金属实例ID")
    physical_machine_id = Column(String(128), nullable=True, comment="物理机ID")
    raid_config = Column(JSON, nullable=True, comment="RAID配置")
    delivery_status = Column(String(32), default="DELIVERED", comment="交付状态，字典表type_code=BAREMETAL_DELIVERY_STATUS")
    install_gpu_driver = Column(
        Boolean,
        default=True,
        comment="是否安装GPU驱动（安装耗时10-20分钟，可能自动重启）"
    )
    # ---------- 状态 ----------
    status = Column(String(32), nullable=False, default="RUNNING", comment="实例状态，字典表type_code=BAREMETAL_INSTANCE_STATUS")
    sync_status = Column(Integer, default=1, comment="资源同步状态：1待执行 2同步中 3成功 4失败")

    # ---------- 审计 ----------
    created_by = Column(Integer, nullable=False, comment="创建人")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )
    last_operation = Column(
        String(50),
        nullable=True,
        comment="最近一次操作，如 START / STOP / REBOOT / CREATE_IMAGE / CLONE / CHANGE_IMAGE / MODIFY_PASSWORD / CHANGE_CHARGE / RELEASE"
    )
    request_params = Column(JSON, nullable=True, comment="用户创建实例时提交的完整参数快照")
    error_message = Column(Text, nullable=True, comment="失败原因")
