from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import CmpBase
from app.core.config import settings

class ClusterNodeResourceHistory(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cluster_node_resource_history"
    __table_args__ = {'comment': '集群节点资源历史记录'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # ---------- 关联信息 ----------
    cluster_id = Column(Integer, nullable=False, index=True, comment="所属集群ID")
    node_id = Column(Integer, nullable=False, index=True, comment="节点ID，对应 cluster_node.id")
    node_name = Column(String(56), nullable=False, comment="节点名称")

    # ---------- 资源 ----------
    cpu_total = Column(Float, nullable=False, comment="节点CPU总核数")
    cpu_used = Column(Float, nullable=False, comment="CPU已使用核数")
    mem_total = Column(Float, nullable=False, comment="节点内存总量，单位GB")
    mem_used = Column(Float, nullable=False, comment="内存已使用，单位GB")
    gpu_total = Column(Integer, nullable=True, comment="GPU总数量")
    gpu_used = Column(Integer, nullable=True, comment="GPU已使用数量")
    gpu_memory_total = Column(Float, nullable=True, comment="GPU总显存，单位GB")
    gpu_memory_used = Column(Float, nullable=True, comment="GPU已使用显存，单位GB")

    pod_count = Column(Integer, nullable=True, default=0, comment="节点上Pod数量")
    pod_used = Column(Integer, nullable=True, default=0, comment="已使用pod数量")

    # ---------- 时间 ----------
    snapshot_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="快照时间（UTC）"
    )
