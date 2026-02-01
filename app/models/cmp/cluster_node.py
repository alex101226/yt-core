from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin

# 集群节点表
class ClusterNode(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cluster_node"
    __table_args__ = {'comment': '集群节点表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    cluster_id = Column(Integer, nullable=False, index=True, comment="所属集群ID")
    node_pool_id = Column(Integer, nullable=False, index=True, comment="所属节点池ID")

    node_name=Column(String(56), nullable=False, comment="节点名称")
    node_id = Column(String(128), nullable=True, comment="云厂商返回的Node ID（或实例ID）")
    instance_id = Column(String(128), nullable=True, comment="对应ECS/BMS实例ID")

    hostname = Column(String(128), nullable=True, comment="节点主机名")

    # ---------- 网络 ----------
    vpc_id = Column(Integer, nullable=True, comment="VPC ID")
    vswitch_id = Column(Integer, nullable=True, comment="子网ID")
    private_ip = Column(String(64), nullable=True, comment="内网IP")
    public_ip = Column(String(64), nullable=True, comment="公网IP")

    # ---------- 规格 ----------
    instance_type = Column(String(20), nullable=True, comment="实例规格类型，例如：如 ecs/bms/lb")
    instance_type_id = Column(String(100), nullable=False, comment="实例规格 ID，如 ecs.g6.large")
    cpu = Column(Integer, nullable=True, comment="CPU核数")
    gpu_memory = Column(Integer, nullable=True, comment="GPU 显存")
    gpu_spec = Column(String(100), nullable=True, comment="GPU类型")
    gpu_amount = Column(Integer, nullable=True, comment="GPU数量")
    system_disk_category = Column(String(50), nullable=False, comment="系统盘类型，例如 ESSD_PL0, SSD")
    system_disk_size = Column(Integer, nullable=False, comment="系统盘大小")

    # ---------- 操作系统 ----------
    image_id = Column(String(100), nullable=False, comment="镜像 ID")
    os_type = Column(String(32), nullable=False, comment="操作系统")
    architecture = Column(String(64), nullable=True, comment="CPU架构")

    status = Column(String(32), nullable=False, default="RUNNING", comment="字典表type_code=NODE_STATUS")

    cordon = Column(Boolean, default=False, comment="是否禁止调度")
    drain = Column(Boolean, default=False, comment="是否已执行驱逐")

    cluster_node_role = Column(String(20), default="WORKER", comment="节点角色，字典：CLUSTER_NODE_ROLE")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="记录创建时间（UTC）"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="记录更新时间（UTC）"
    )
