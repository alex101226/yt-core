# app/models/cmp/instance_create_task.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings


class InstanceCreateTask(CmpBase):
    """
    服务器主创建任务表
    记录一次创建 ECS 实例的整体过程
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}instance_create_task"
    __table_args__ = {"comment": "服务器主创建任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, nullable=False, comment="提交创建的用户 ID")
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    region_id = Column(String(50), nullable=False, comment="地域 ID")
    zone_id = Column(String(50), nullable=True, comment="可用区 ID")

    instance_id = Column(String(100), nullable=True, comment="云厂商返回的实例 ID")
    instance_name = Column(String(100), nullable=False, comment="实例名称")
    instance_type = Column(String(100), nullable=False, comment="实例规格 ID，如 ecs.g6.large")
    image_id = Column(String(100), nullable=False, comment="镜像 ID")
    system_disk_category = Column(String(50), nullable=False, comment="系统盘类型，例如 ESSD_PL0, SSD")
    system_disk_size = Column(Integer, nullable=False, comment="系统盘大小")
    data_disks = Column(JSON, nullable=True, comment="数据盘列表")

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

    internet_charge_type = Column(String(30), nullable=True, comment="公网计费类型：PayByBandwidth/PayByTraffic")
    internet_max_bandwidth_out = Column(Integer, nullable=True, comment="公网最大带宽（Mbps）")

    vpc_id = Column(String(100), nullable=True, comment="VPC ID")
    vswitch_id = Column(String(100), nullable=True, comment="交换机 ID")
    public_ip = Column(String(50), nullable=True, comment="分配的公网 IP（可选）")
    private_ip= Column(String(50), nullable=True, comment="私网 IP（可选）")

    security_group_id = Column(String(100), nullable=True, comment="安全组 ID")

    hostname = Column(String(100), nullable=True, comment="主机名，可选")
    description = Column(Text, nullable=True, comment="实例描述，可选")
    password = Column(String(100), nullable=True, comment="管理密码（可选，如果用密钥登录则为空）")
    key_pair_name = Column(String(100), nullable=True, comment="SSH 密钥名称（可选）")
    enable_ssh_agent = Column(Boolean, default=False, comment="是否开启 SSH 代理")
    ssh_proxy_port = Column(Integer, default=False, comment="SSH 代理端口")
    login_mode = Column(String(20), nullable=False, default="PASSWORD", comment="登录方式：PASSWORD / KEYPAIR")
    enable_protection = Column(Boolean, default=False, comment="是否开启释放保护")
    last_operation = Column(
        String(50),
        nullable=True,
        comment="最近一次操作，如 START / STOP / REBOOT / CREATE_IMAGE / CLONE / CHANGE_IMAGE / MODIFY_PASSWORD / CHANGE_CHARGE / RELEASE"
    )

    sync_status = Column(Integer, default=1, comment="资源同步状态：1待执行 2同步中 3成功 4失败")
    request_params = Column(JSON, nullable=True, comment="用户创建实例时提交的完整参数快照")

    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="实例状态：1初始化 2运行中 3创建准备 4创建中 5创建失败 6准备关机 7关机中 8已关机"
    )
    error_message = Column(Text, nullable=True, comment="失败原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
