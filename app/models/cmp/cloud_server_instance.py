# app/models/cmp/cloud_server_instance.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

from .is_released_mixin import IsReleasedMixin


class CloudServerInstance(CmpBase, IsReleasedMixin):
    """
    服务器主创建任务表
    记录一次创建 ECS 实例的整体过程
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cloud_server_instance"
    __table_args__ = {"comment": "服务器主创建任务表"}

    # ---------- 基础信息 ----------
    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_name = Column(String(100), nullable=False, comment="实例名称")
    hostname = Column(String(100), nullable=True, comment="主机名，可选")
    description = Column(Text, nullable=True, comment="实例描述，可选")

    # ---------- 云 & 账号 ----------
    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    region_id = Column(String(50), nullable=False, comment="地域 ID")
    zone_id = Column(String(50), nullable=True, comment="可用区 ID")
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")

    # ---------- 规格 ----------
    instance_type = Column(String(20), nullable=True, comment="实例规格类型，例如：如 ecs/bms/lb")
    instance_type_id = Column(String(100), nullable=False, comment="实例规格 ID，如 ecs.g6.large")
    cpu = Column(Integer, nullable=True, comment="CPU核数")
    gpu = Column(Integer, nullable=True, comment="GPU核数")
    system_disk_category = Column(String(50), nullable=False, comment="系统盘类型，例如 ESSD_PL0, SSD")
    system_disk_size = Column(Integer, nullable=False, comment="系统盘大小")
    data_disks = Column(JSON, nullable=True, comment="数据盘列表")

    # ---------- 操作系统 ----------
    image_id = Column(String(100), nullable=False, comment="镜像 ID")
    os_type = Column(String(32), nullable=False, comment="操作系统")
    os_version = Column(String(64), nullable=True, comment="操作系统版本")

    # ---------- 网络 ----------
    vpc_id = Column(String(100), nullable=True, comment="VPC ID")
    vswitch_id = Column(String(100), nullable=True, comment="交换机 ID")
    public_ip = Column(String(50), nullable=True, comment="分配的公网 IP（可选）")
    private_ip = Column(String(50), nullable=True, comment="私网 IP（可选）")
    internet_max_bandwidth_out = Column(Integer, nullable=True, comment="公网最大带宽（Mbps）")

    # ---------- 安全 ----------
    security_group_id = Column(String(100), nullable=True, comment="安全组 ID")
    hashed_password = Column(String(100), nullable=True, comment="管理密码（可选，如果用密钥登录则为空）")
    key_pair_name = Column(String(100), nullable=True, comment="SSH 密钥名称（可选）")
    enable_ssh_agent = Column(Boolean, default=False, comment="是否开启 SSH 代理")
    ssh_proxy_port = Column(Integer, default=False, comment="SSH 代理端口")
    login_mode = Column(String(20), nullable=False, default="PASSWORD", comment="登录方式：PASSWORD / KEYPAIR")
    enable_protection = Column(Boolean, default=False, comment="是否开启释放保护")

    # ---------- 计费 ----------
    internet_charge_type = Column(String(30), nullable=True, comment="公网计费类型：PayByBandwidth/PayByTraffic")
    instance_charge_type = Column(String(10),  nullable=False, comment="实例计费类型:PrePaid（包年包月）/PostPaid（按量付费）")
    period = Column(
        Integer,
        nullable=True,
        comment="包年包月购买时长（单位：月），仅在 instance_charge_type=PrePaid 时有效"
    )
    spot_strategy = Column(
        String(20),
        nullable=True,
        comment="抢占式策略：NoSpot（非抢占式）/ SpotWithPriceLimit（竞价抢占式）/ SpotAsPriceGo（按当前价格抢占式）"
    )
    quantity = Column(Integer, default=1, comment="购买数量")
    auto_renew = Column(Boolean, default=False, comment="是否到期自动续费(仅包年包月)")

    # ---------- 状态 ----------
    sync_status = Column(Integer, default=1, comment="资源同步状态：1待执行 2同步中 3成功 4失败")
    status = Column(
        String(50),
        nullable=False,
        default="INIT",
        comment="实例状态：字典表里的type_code=SERVER_STATUS"
    )

    # ---------- 云服务器特有 ----------
    instance_id = Column(String(100), nullable=True, comment="云厂商返回的实例 ID")

    # ---------- 审计 ----------
    created_by = Column(Integer, nullable=False, comment="提交创建的用户 ID")
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