from nanoid import generate
from app.core.logger import logger

from app.repositories.cmp.cluster_repo import ClusterRepository, NodePoolRepository, NodeRepository
from app.schemas.cmp.cluster_schema import ClusterCreateSchema, NodePoolCreateSchema, NodeCreateSchema

class ClusterService:
    def __init__(self, db):
        self.db = db
        self.cluster_repo = ClusterRepository(db)
        self.node_pool_repo = NodePoolRepository(db)
        self.node_repo = NodeRepository(db)


    # 创建集群
    def create_cluster_full(self, user_id: int, cluster_data: ClusterCreateSchema):
        # -----------------------
        # 1. 创建集群
        # -----------------------
        cluster_id = f"cluster-{generate(size=12)}"
        payload_dict = cluster_data.model_dump()
        cluster_payload = {
            "cluster_name": cluster_data.cluster_name,
            "region_id": cluster_data.region_id,
            "zone_id": cluster_data.zone_id,
            "provider_code": cluster_data.provider_code,
            "resource_group_id": cluster_data.resource_group_id,
            "charge_type": cluster_data.charge_type,
            "period": cluster_data.period,
            "auto_renew": cluster_data.auto_renew,
            "cluster_spec": cluster_data.cluster_spec,
            "master_count": cluster_data.master_count,
            "cluster_version": cluster_data.cluster_version,
            "network_type": cluster_data.network_type,
            "vpc_id": cluster_data.vpc_id,
            "subnet_ids": cluster_data.subnet_ids,
            "security_group_id": cluster_data.security_group_id,
            "service_cidr": cluster_data.service_cidr,
            "deletion_protection": cluster_data.deletion_protection,
            "tags": cluster_data.tags,
            "created_by": user_id,
            "cluster_id": cluster_id
        }
        cluster = self.cluster_repo.create(cluster_payload)

        # -----------------------
        # 2. 创建节点池
        # -----------------------
        node_pools_data = payload_dict.pop("node_pools", [])
        node_pools = self.node_pool_repo.create_batch(cluster.id, node_pools_data)

        # -----------------------
        # 3. 创建节点
        # -----------------------
        for node_pool in node_pools:
            #  hhhh <app.models.cmp.cluster_node_pool.ClusterNodePool object at 0x113e0cf10>
            # logger.info(f'hhhh {node_pool}')
            # 假设节点数量 = desired_size，节点实例ID直接生成uuid模拟
            node_list = []
            for i in range(node_pool.desired_size):
                node_payload = {
                    "cluster_id": cluster.id,
                    "node_pool_id": node_pool.id,
                    "instance_id": f"ECS-{generate(size=6)}",
                    "node_id": f"node-{generate(size=12)}",
                    # "node_name": f"{node_pool.pool_name}-node-{i + 1}",
                    # "instance_type": node_pool.instance_types[0],
                    "os_image": node_pool.image_id,
                    "cluster_node_role": "WORKER",
                }
                node_list.append(node_payload)
            self.node_repo.create_batch(node_list)

        self.db.commit()
        self.db.refresh(cluster)
        return cluster
