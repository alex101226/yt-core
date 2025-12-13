from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON

from app.core.config import settings
from app.core.database import CmpBase
from .is_released_mixin import IsReleasedMixin

# 集群节点池表
class ClusterNodePool(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cluster_node_pool"
    __table_args__ = {'comment': '集群节点池表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    cluster_id = Column(Integer, nullable=False, index=True, comment="所属集群ID")
    pool_name = Column(String(64), nullable=False, comment="节点池名称")
    node_pool_type = Column(String(20), default="NODE_POOL_TYPE", comment="节点池类型，字典：NODE_POOL_TYPE")

    node_type = Column(String(32), nullable=False, comment="节点类型：ecs/bms")
    instance_types = Column(JSON, nullable=False, comment="可选实例规格列表(JSON 数组)")


    # 计费方式
    charge_type = Column(String(32), nullable=False, comment="计费方式：PostPaid/PrePaid")
    period = Column(Integer, nullable=True, comment="包年包月时长（月单位），按量付费可为空")
    auto_renew = Column(Boolean, default=False, comment="是否开启自动续费")

    desired_size = Column(Integer, nullable=False, comment="期望节点数")
    min_size = Column(Integer, nullable=False, default=1, comment="最小节点数")
    max_size = Column(Integer, nullable=False, default=10, comment="最大节点数")

    scaling_policy = Column(String(32), nullable=True, comment="扩缩容策略，字典表type_code=SCALING_POLICY")
    auto_repair = Column(Boolean, default=True, comment="异常节点自动替换")

    image_id = Column(String(128), nullable=False, comment="系统镜像ID")
    system_disk_type = Column(String(32), nullable=False, comment="系统盘类型，如 cloud_ssd")
    system_disk_size = Column(Integer, nullable=False, comment="系统盘大小 GB")

    admin_password = Column(String(128), nullable=True, comment="节点管理员密码（加密后）")
    labels = Column(JSON, nullable=True, comment="节点池通用标签")
    taints = Column(JSON, nullable=True, comment="污点配置")

    status = Column(String(32), nullable=False, default="RUNNING", comment="字典表type_code=NODE_POOL_STATUS")

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
