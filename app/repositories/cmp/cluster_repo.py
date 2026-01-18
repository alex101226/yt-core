from sqlalchemy.orm import Session
from typing import List
from app.models.cmp.k8s_cluster import K8sCluster
from app.models.cmp.cluster_node_pool import ClusterNodePool
from app.models.cmp.cluster_node import ClusterNode

from app.schemas.cmp.cluster_schema import ClusterCreateSchema, NodePoolCreateSchema, NodeCreateSchema

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
        return cluster


# -------------------
# 节点池 Repository
# -------------------
class NodePoolRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, cluster_id: int, node_pool: dict) -> list:
        node_pool = ClusterNodePool(**node_pool)
        self.db.add(node_pool)
        self.db.flush()
        return node_pool

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
