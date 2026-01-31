from datetime import datetime, timezone
import random

from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.logger import logger
from app.models.cmp.cluster_k8s import K8sCluster
from app.models.cmp.cluster_node_pool import ClusterNodePool
from app.models.cmp.cluster_node import ClusterNode
from app.models.cmp.cluster_node_resource_history import ClusterNodeResourceHistory

from app.models.cmp.resource_group import ResourceGroup
from app.models.cmp.vpc import Vpc
from app.models.cmp.subnet import Subnet

# -------------------
# 集群 Repository
# -------------------
class ClusterRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建集群
    def create(self, cluster_data: dict) -> K8sCluster:
        cluster = K8sCluster(**cluster_data)
        self.db.add(cluster)
        self.db.flush()  # 获取 cluster.id
        logger.info(f'创建成功了吗=========》〉》〉 {cluster.id}')
        return cluster

    # 根据集群ID统计资源使用情况
    def get_cluster_resource_usage(self, cluster_id: int):
        """
        返回：
            {
                "cpu_total": float,
                "cpu_used": float,
                "mem_total": float,
                "mem_used": float,
                "pod_total": int,
                "pod_used": int
            }
        """
        # 1️⃣ 获取每个节点最新快照的子查询
        latest_snapshots_subq = (
            self.db.query(
                ClusterNodeResourceHistory.node_id,
                func.max(ClusterNodeResourceHistory.snapshot_time).label("latest_time")
            )
            .filter(ClusterNodeResourceHistory.cluster_id == cluster_id)
            .group_by(ClusterNodeResourceHistory.node_id)
            .subquery()
        )

        # 2️⃣ 关联最新快照获取资源使用量
        latest_resources = (
            self.db.query(ClusterNodeResourceHistory)
            .join(
                latest_snapshots_subq,
                (ClusterNodeResourceHistory.node_id == latest_snapshots_subq.c.node_id) &
                (ClusterNodeResourceHistory.snapshot_time == latest_snapshots_subq.c.latest_time)
            )
            .subquery()
        )

        # 3️⃣ 聚合统计
        result = self.db.query(
            func.round(func.sum(ClusterNode.cpu), 2).label("cpu_total"),
            func.round(func.sum(latest_resources.c.cpu_used), 2).label("cpu_used"),
            func.round(func.sum(ClusterNode.system_disk_size), 2).label("mem_total"),
            func.round(func.sum(latest_resources.c.mem_used), 2).label("mem_used"),
            func.round(func.sum(latest_resources.c.pod_count), 2).label("pod_used"),
            func.round(func.sum(ClusterNodeResourceHistory.pod_count), 2).label("pod_total"),
        ).join(
            latest_resources,
            ClusterNode.id == latest_resources.c.node_id
        ).filter(
            ClusterNode.cluster_id == cluster_id
        ).one()

        return {
            "cpu_total": float(result.cpu_total or 0),
            "cpu_used": float(result.cpu_used or 0),
            "mem_total": float(result.mem_total or 0),
            "mem_used": float(result.mem_used or 0),
            "pod_total": int(result.pod_total or 0),
            "pod_used": int(result.pod_used or 0),
        }

    # 集群查询
    def cluster_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        name: Optional[str] = None,
    ):
        query = ((self.db.query(
            K8sCluster,
            Vpc.vpc_name.label("vpc_name"),
            ResourceGroup.rg_name.label("resource_group_name"),
            func.group_concat(Subnet.subnet_name).label("subnet_name")
        ).outerjoin(
            ResourceGroup,
            K8sCluster.resource_group_id == ResourceGroup.id
        ).outerjoin(
            Vpc, K8sCluster.vpc_id == Vpc.id
        ).outerjoin(
            Subnet,
            func.find_in_set(
                func.cast(Subnet.id, String),
                func.replace(
                    func.replace(K8sCluster.subnet_ids, '["', ''),
                    '"]', ''
                )
            )
        ))
                 .group_by(K8sCluster.id)
                 .order_by(K8sCluster.id.desc()))

        filters = [
            K8sCluster.created_by == user_id,
            K8sCluster.is_released == 0,
        ]
        if name:
            filters.append(K8sCluster.cluster_name.like(f"%{name}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.offset(offset_value).limit(page_size).all()
        return items, total


# -------------------
# 节点池 Repository
# -------------------
class NodePoolRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, node_pool: dict) -> list:
        node_pool = ClusterNodePool(**node_pool)
        self.db.add(node_pool)
        self.db.flush()
        return node_pool

    # 节电池列表
    def cluster_pool_list(self, cluster_id: int):
        query = self.db.query(ClusterNodePool).filter(ClusterNodePool.cluster_id == cluster_id)
        return query.all()

# -------------------
# 节点 Repository
# -------------------
class NodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, node_data: dict) -> ClusterNode:
        node = ClusterNode(**node_data)
        self.db.add(node)
        self.db.flush()  # 获取 node.id
        return node

    def create_batch(self, node_list: list) -> list:
        nodes = []
        for node_data in node_list:

            node = self.create(node_data)
            nodes.append(node)
        self.db.flush()
        return nodes

    # 节点列表
    def cluster_node_list(self, cluster_id: int, pool_id: Optional[int] = None):
        query = (self.db.query(
            ClusterNode,
            ClusterNodePool.charge_type,
        ).outerjoin(
            ClusterNodePool,
            ClusterNodePool.id == ClusterNode.node_pool_id
        ).filter(ClusterNode.cluster_id == cluster_id).order_by(ClusterNode.id.desc()))
        # 可选条件
        if pool_id:
            query = query.filter(ClusterNode.node_pool_id == pool_id)
        return query.all()

# 节点资源使用情况
class NodeResourceHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def node_resource_create(self, data: dict):
        history = ClusterNodeResourceHistory(**data)
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def push_fake_resources_for_cluster(self, cluster_id: int):
        nodes = self.db.query(ClusterNode).filter(ClusterNode.cluster_id == cluster_id).all()
        now = datetime.now(timezone.utc)

        for node in nodes:
            # CPU/内存/Pod总量
            cpu_total = node.cpu or 0
            mem_total = node.system_disk_size or 0  # 内存就是 system_disk_size
            pod_total = node.id * 10  # 每个节点固定Pod总量
            gpu_total = node.gpu_amount or 0
            gpu_memory_total = node.gpu_memory or 0

            # 随机生成已使用量   (func.count(ClusterNode.id) * 10).label("pod_total"),
            cpu_used = round(random.uniform(0, cpu_total), 2) if cpu_total else 0
            mem_used = round(random.uniform(0, mem_total), 2) if mem_total else 0
            pod_used = random.randint(0, pod_total)  # 已使用 Pod
            gpu_used = random.randint(0, gpu_total) if gpu_total else 0
            gpu_memory_used = round(random.uniform(0, gpu_memory_total), 2) if gpu_memory_total else 0
            # 构建历史记录
            data = {
                "cluster_id": cluster_id,
                "node_id": node.id,
                "node_name": node.node_name,
                "cpu_total": cpu_total,
                "cpu_used": cpu_used,
                "mem_total": mem_total,
                "mem_used": mem_used,
                "gpu_total": gpu_total,
                "gpu_used": gpu_used,
                "gpu_memory_total": gpu_memory_total,
                "gpu_memory_used": gpu_memory_used,
                "pod_count": pod_total,
                "pod_used": pod_used,
                "snapshot_time": now,
            }

            self.node_resource_create(data)
