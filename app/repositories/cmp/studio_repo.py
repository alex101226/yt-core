from typing import Optional

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.cmp.cluster_k8s import K8sCluster
from app.models.cmp.cluster_node import ClusterNode
from app.models.cmp.cluster_node_pool import ClusterNodePool
from app.models.cmp.resource_group import ResourceGroup
from app.models.cmp.studio import Studio


class StudioRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: dict) -> Studio:
        studio = Studio(**payload)
        self.db.add(studio)
        self.db.flush()
        return studio

    def get_by_cluster_id(self, cluster_id: int) -> Optional[Studio]:
        return (
            self.db.query(Studio)
            .filter(Studio.cluster_id == cluster_id, Studio.is_released == 0)
            .first()
        )

    def get_by_id(self, studio_id: int) -> Optional[Studio]:
        return (
            self.db.query(Studio)
            .filter(Studio.id == studio_id, Studio.is_released == 0)
            .first()
        )

    def studio_page_list(
        self,
        owner_user_id: Optional[int],
        page: int,
        page_size: int,
        studio_name: Optional[str] = None,
    ):
        query = (
            self.db.query(
                Studio,
                K8sCluster,
                ResourceGroup.rg_name.label("resource_group_name"),
            )
            .join(K8sCluster, K8sCluster.id == Studio.cluster_id)
            .outerjoin(ResourceGroup, ResourceGroup.id == K8sCluster.resource_group_id)
            .filter(
                Studio.is_released == 0,
                K8sCluster.is_released == 0,
            )
            .order_by(Studio.id.desc())
        )
        if owner_user_id is not None:
            query = query.filter(Studio.created_by == owner_user_id)
        if studio_name:
            query = query.filter(Studio.studio_name.like(f"%{studio_name}%"))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def studio_list(self, owner_user_id: Optional[int]):
        query = (
            self.db.query(Studio.id, Studio.studio_name)
            .join(K8sCluster, K8sCluster.id == Studio.cluster_id)
            .filter(
                Studio.is_released == 0,
                K8sCluster.is_released == 0,
            )
            .order_by(Studio.id.desc())
        )
        if owner_user_id is not None:
            query = query.filter(Studio.created_by == owner_user_id)
        return query.all()

    def get_accessible_studios(self, owner_user_id: Optional[int]):
        query = (
            self.db.query(Studio, K8sCluster)
            .join(K8sCluster, K8sCluster.id == Studio.cluster_id)
            .filter(
                Studio.is_released == 0,
                K8sCluster.is_released == 0,
            )
            .order_by(Studio.id.desc())
        )
        if owner_user_id is not None:
            query = query.filter(Studio.created_by == owner_user_id)
        return query.all()

    def studio_node_page_list(
        self,
        owner_user_id: Optional[int],
        studio_id: Optional[int],
        page: int,
        page_size: int,
        node_name: Optional[str] = None,
    ):
        query = (
            self.db.query(
                ClusterNode,
                Studio.id.label("studio_id"),
                Studio.studio_name,
                ClusterNodePool.charge_type,
                ClusterNodePool.node_type,
            )
            .join(Studio, Studio.cluster_id == ClusterNode.cluster_id)
            .outerjoin(ClusterNodePool, ClusterNodePool.id == ClusterNode.node_pool_id)
            .filter(
                Studio.is_released == 0,
                ClusterNode.is_released == 0,
            )
            .order_by(ClusterNode.id.desc())
        )
        if owner_user_id is not None:
            query = query.filter(Studio.created_by == owner_user_id)
        if studio_id is not None:
            query = query.filter(Studio.id == studio_id)
        if node_name:
            query = query.filter(ClusterNode.node_name.like(f"%{node_name}%"))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_node_stats(self, cluster_id: int):
        row = (
            self.db.query(
                func.count(ClusterNode.id).label("total_nodes"),
                func.sum(case((ClusterNode.status == "RUNNING", 1), else_=0)).label("healthy_nodes"),
                func.coalesce(func.sum(ClusterNode.gpu_amount), 0).label("gpu_total"),
            )
            .filter(
                ClusterNode.cluster_id == cluster_id,
                ClusterNode.is_released == 0,
            )
            .one()
        )
        return {
            "total_nodes": int(row.total_nodes or 0),
            "healthy_nodes": int(row.healthy_nodes or 0),
            "gpu_total": int(row.gpu_total or 0),
        }
