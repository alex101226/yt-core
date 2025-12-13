from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON

from app.core.config import settings
from app.core.database import CmpBase
from .is_released_mixin import IsReleasedMixin

# 集群节点表
class ClusterNode(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cluster_node"
    __table_args__ = {'comment': '集群节点表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    cluster_id = Column(Integer, nullable=False, index=True, comment="所属集群ID")
    node_pool_id = Column(Integer, nullable=False, index=True, comment="所属节点池ID")

    node_id = Column(String(128), nullable=True, comment="云厂商返回的Node ID（或实例ID）")
    instance_id = Column(String(128), nullable=True, comment="对应ECS/BMS实例ID")

    hostname = Column(String(128), nullable=True, comment="节点主机名")
    private_ip = Column(String(64), nullable=True, comment="内网IP")
    public_ip = Column(String(64), nullable=True, comment="公网IP")

    cpu = Column(Integer, nullable=True, comment="CPU核数")
    memory = Column(Integer, nullable=True, comment="内存大小（MB）")
    os_image = Column(String(128), nullable=True, comment="镜像ID（实际）")

    status = Column(String(32), nullable=False, default="RUNNING", comment="字典表type_code=NODE_STATUS")

    labels = Column(JSON, nullable=True, comment="实际节点标签")
    taints = Column(JSON, nullable=True, comment="实际节点污点")

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
