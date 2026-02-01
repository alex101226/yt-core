from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin

"""
Kubernetes 集群基本信息表
"""
class K8sCluster(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cluster_k8s"
    __table_args__ = {'comment': 'Kubernetes 集群'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 基础标识
    cluster_id = Column(String(64), unique=True, nullable=False, comment="云厂商返回的集群 ID")
    cluster_name = Column(String(128), nullable=False, comment="集群名称")

    # 云环境
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商，如 aliyun/tencent/aws")
    region_id = Column(String(64), nullable=False, comment="区域 ID")
    zone_id = Column(String(64), nullable=False, comment="可用区 ID")
    resource_group_id = Column(String(64), nullable=True, comment="资源组 ID")

    # 计费方式
    charge_type = Column(String(32), nullable=False, comment="计费方式：PostPaid/PrePaid")
    period = Column(Integer, nullable=True, comment="包年包月时长（月单位），按量付费可为空")
    auto_renew = Column(Boolean, default=False, comment="是否开启自动续费")

    # 集群配置
    cluster_version = Column(String(32), nullable=False, comment="K8s 版本")
    cluster_type = Column(String(32), default="managed", comment="集群类型：managed/self_managed/edge")

    # 控制平面
    master_count = Column(Integer, default=1, comment="Master 节点数量")
    master_instance_type = Column(String(64), nullable=True, comment="Master 实例规格（如果支持）")

    # 网络
    vpc_id = Column(String(64), nullable=False, comment="VPC ID")
    subnet_ids = Column(JSON, nullable=False, comment="子网 ID 列表")
    security_group_id = Column(String(64), nullable=True, comment="安全组 ID")
    network_type = Column(String(32), default="vpc", comment="网络类型：vpc/terway/global_router")

    service_cidr = Column(String(64), nullable=False, comment="Service CIDR")
    pod_cidr = Column(String(64), nullable=True, comment="Pod CIDR（有些云自动分配）")
    enable_public_api = Column(Boolean, default=False, comment="是否开启公网访问 API Server")

    # 删除保护
    deletion_protection = Column(Boolean, default=False, comment="删除保护")

    # 标签
    tags = Column(JSON, nullable=True, comment="标签（KeyValue 数组）")

    # 元数据
    status = Column(String(32), default="RUNNING", comment="字典表type_code=CLUSTER_STATUS")
    message = Column(String(512), nullable=True, comment="状态信息，用于错误记录")

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
