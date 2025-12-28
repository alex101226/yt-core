from nanoid import generate
from app.core.logger import logger

from app.core.security import hash_password
from app.common.ipaddress import allocate_private_ip

from app.repositories.cmp.cluster_repo import ClusterRepository, NodePoolRepository, NodeRepository
from app.schemas.cmp.cluster_schema import ClusterCreateSchema, NodePoolCreateSchema, NodeCreateSchema

class ClusterService:
    def __init__(self, db):
        self.db = db
        self.cluster_repo = ClusterRepository(db)
        self.node_pool_repo = NodePoolRepository(db)
        self.node_repo = NodeRepository(db)


    # 创建集群
    def create_cluster_full(self, user_id: int, cluster_data: dict):
        logger.info(f'查看接收到的参数 {cluster_data}')
        # -----------------------
        # 1. 创建集群
        # -----------------------
        node_pool_data = cluster_data.get('node_pools', {})

        cluster_id = f"cluster-{generate(size=12)}"
        # payload_dict = cluster_data.model_dump()
        cluster_payload = {
            "cluster_name": cluster_data['cluster_name'],
            "region_id": cluster_data['region_id'],
            "zone_id": cluster_data['zone_id'],
            "provider_code": cluster_data['provider_code'],
            "resource_group_id": cluster_data['resource_group_id'],
            "charge_type": cluster_data['charge_type'],
            "period": cluster_data['period'],
            "auto_renew": cluster_data['auto_renew'],
            # "cluster_spec": cluster_data['cluster_spec'],
            "master_count": node_pool_data['desired_size'],
            "cluster_version": cluster_data['cluster_version'],
            "network_type": cluster_data['network_type'],
            "vpc_id": cluster_data['vpc_id'],
            "subnet_ids": cluster_data['subnet_ids'],
            "security_group_id": cluster_data['security_group_id'],
            "service_cidr": cluster_data['service_cidr'],
            "deletion_protection": cluster_data['deletion_protection'],
            "tags": cluster_data['tags'],
            "created_by": user_id,
            "cluster_id": cluster_id,
            "price": cluster_data.get('price', 0),
        }
        cluster = self.cluster_repo.create(cluster_payload)

        # -----------------------
        # 2. 创建节点池
        # -----------------------
        instance_types = cluster_data.get('instance_types', [])

        created_node_pools = []

        for inst_spec in instance_types:
            # 每个实例规格创建一个节点池
            payload = {
                "cluster_id": cluster.id,
                "pool_name": node_pool_data.get("pool_name"),
                "node_type": node_pool_data["node_type"],
                "charge_type": node_pool_data["charge_type"],
                "period": node_pool_data.get("period", 0),
                "auto_renew": node_pool_data.get("auto_renew", False),
                "desired_size": node_pool_data["desired_size"],
                "scaling_policy": node_pool_data.get("scaling_policy"),
                "auto_repair": node_pool_data.get("auto_repair", True),
                "image_id": node_pool_data["image_id"],
                "system_disk_category": node_pool_data["system_disk_category"],  # 统一字段名
                "system_disk_size": node_pool_data["system_disk_size"],
                "admin_password": hash_password(node_pool_data.get("admin_password")),
                "labels": node_pool_data.get("labels", []),
                "taints": node_pool_data.get("taints", []),
                "instance_type_id": inst_spec["instance_type_id"],  # 保存对应实例规格ID
                "price": node_pool_data.get('price', 0),
            }
            # node_pool = ClusterNodePool(**payload)
            # self.db.add(node_pool)
            # self.db.flush()  # 获取 node_pool.id
            node_pool = self.node_pool_repo.create_batch(cluster.id, payload)
            created_node_pools.append((node_pool, inst_spec))  # 同时保留实例规格信息

        # node_pools = self.node_pool_repo.create_batch(cluster.id, node_pools_data)

        # -----------------------
        # 3. 创建节点
        # -----------------------
        for node_pool, inst_spec in created_node_pools:
            # 假设节点数量 = desired_size，节点实例ID直接生成uuid模拟
            node_list = []
            for i in range(node_pool.desired_size):
                node_payload = {
                    "cluster_id": cluster.id,
                    "node_pool_id": node_pool.id,
                    "instance_id": f"ECS-{generate(size=6)}",
                    "node_id": f"node-{generate(size=12)}",
                    "node_name": f"{node_pool.pool_name}-node-{i + 1}",
                    "os_type": node_pool_data["os_type"],
                    "image_id": node_pool.image_id,
                    "instance_type": inst_spec.get("instance_family", ""),
                    "instance_type_id": inst_spec["instance_type_id"],
                    "cpu": inst_spec.get("cpu_core_count"),
                    "gpu_amount": inst_spec.get("gpu_amount"),
                    "gpu_spec": inst_spec.get("gpu_spec"),
                    "gpu_memory": inst_spec.get("gpu_memory"),
                    "architecture": inst_spec.get("architecture"),
                    "system_disk_category": node_pool.system_disk_category,
                    "system_disk_size": node_pool.system_disk_size,
                    "cluster_node_role": "WORKER",
                    "private_ip":  allocate_private_ip(cluster_data['service_cidr'], [])
                }
                node_list.append(node_payload)
            self.node_repo.create_batch(node_list)

        self.db.commit()
        self.db.refresh(cluster)
        return cluster
