from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger
from app.core.security import hash_password
from app.common.ipaddress import allocate_private_ip


from app.services.cmp.subnet_service import SubnetService
from app.services.cmp.vpc_service import VPCService

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.repositories.cmp.cluster_repo import (
ClusterRepository, NodePoolRepository, NodeRepository, NodeResourceHistoryRepository
)
from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.cmp.studio_repo import StudioRepository

from app.services.cmp.operation_helper import execute_with_notification


class ClusterService:
    def __init__(self, db):
        self.db = db
        self.cluster_repo = ClusterRepository(db)
        self.node_pool_repo = NodePoolRepository(db)
        self.node_repo = NodeRepository(db)
        self.node_history_repo = NodeResourceHistoryRepository(db)
        self.studio_repo = StudioRepository(db)
        self.member_repo = MemberRepository(db)
        self.account_service = AccountService(self.db)
        self.bill_service = BillService(db)
        self.vpc_service = VPCService(db)
        self.subnet_service = SubnetService(db)

    def _resolve_member_id(self, user: dict):
        user_id = user.get("user_id")
        parent_id = user.get("parent_id") or 0
        owner_user_id = user_id if parent_id == 0 else parent_id
        member = self.member_repo.get_by_user_id(owner_user_id)
        return member.id if member else None

    # 生成计费任务
    def create_initial_bill(
        self,
        user: dict,
        charge_type: str,
        instance_id: str,
        unit_price: float,
        instance,
    ):
        account = self.account_service.owner_account_exists(user)
        if not account:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="CLUSTER",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建集群
    def create_cluster_full(self, user: dict, cluster_data: dict):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            try:
                with self.db.begin():
                    node_pool_data = cluster_data.get('node_pools', {})

                    cluster_id = f"cluster-{generate(size=12)}"

                    cluster_payload = {
                        "cluster_name": cluster_data['cluster_name'],
                        "region_id": cluster_data['region_id'],
                        "zone_id": cluster_data['zone_id'],
                        "cloud_provider_code": cluster_data['provider_code'],
                        "resource_group_id": cluster_data['resource_group_id'],
                        "charge_type": cluster_data['charge_type'],
                        "period": cluster_data['period'],
                        "auto_renew": cluster_data['auto_renew'],
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
                        "created_by_name": username,
                        "cluster_id": cluster_id,
                        # "price": cluster_data.get('price', 0),
                    }
                    cluster = self.cluster_repo.create(cluster_payload)
                    if not self.studio_repo.get_by_cluster_id(cluster.id):
                        self.studio_repo.create({
                            "cluster_id": cluster.id,
                            "studio_name": cluster.cluster_name,
                            "instance_id": generate(size=8),
                            "studio_type": "基础版",
                            "member_id": self._resolve_member_id(user),
                            "resource_group_id": cluster.resource_group_id,
                            "enabled": True,
                            "status": "ENABLED",
                            "created_by": user_id,
                            "created_by_name": username,
                        })

                    self.create_initial_bill(
                        user, cluster_payload['charge_type'], cluster_id, cluster_data['price'], cluster,
                    )
                    # 2. 创建节点池
                    instance_types = node_pool_data.get('instance_types', [])

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
                            # "price": node_pool_data.get('price', 0),
                            "cpu": inst_spec.get("cpu_core_count"),
                            "gpu_amount": inst_spec.get("gpu_amount"),
                            "gpu_spec": inst_spec.get("gpu_spec"),
                            "gpu_memory": inst_spec.get("gpu_memory"),
                            "instance_type": inst_spec["instance_family"],
                            "instance_type_id": inst_spec["instance_type_id"],
                            "node_pool_type": "MASTER",
                            "created_by": user_id,
                            "created_by_name": username,
                        }
                        node_pool = self.node_pool_repo.create_batch(payload)
                        created_node_pools.append((node_pool, inst_spec))  # 同时保留实例规格信息

                    # 3. 创建节点
                    for node_pool, inst_spec in created_node_pools:
                        desired_size = int(node_pool.desired_size)
                        # 假设节点数量 = desired_size，节点实例ID直接生成uuid模拟
                        node_list = []
                        for i in range(desired_size):
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
                                "private_ip": allocate_private_ip(cluster_data['service_cidr'], []),
                                "created_by": user_id,
                                "created_by_name": username,
                            }
                            node_list.append(node_payload)
                        self.node_repo.create_batch(node_list)
                return cluster
            except BusinessException as exception:
                self.db.rollback()
                raise exception

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="CLUSTER",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="集群创建成功",
            failed_desc="集群创建失败",
            func=_do
        )

    # 集群列表
    def cluster_page_list(self, user: dict, page: int, page_size: int, name: str):

        parent_id = user.get('parent_id') or 0
        if parent_id == 0:
            parent_id = user.get('user_id')
        # user_id = user.get('user_id')

        items, total = self.cluster_repo.cluster_page_list(parent_id, page, page_size, name)

        # 在获取集群列表时写入节点资源历史
        for cluster, vpc_name, rg_name, subnet_name in items:
            self.node_history_repo.push_fake_resources_for_cluster(cluster.id)

        result_items = []
        for cluster, vpc_name, rg_name, subnet_name in items:
            resource_info = self.cluster_repo.get_cluster_resource_usage(cluster.id)
            item = {
                "id": cluster.id,
                "cluster_name": cluster.cluster_name,
                "cluster_id": cluster.cluster_id,
                "vpc_id": cluster.vpc_id,
                "resource_group_id": cluster.resource_group_id,
                "subnet_ids": cluster.subnet_ids,
                "vpc_name": vpc_name,
                "resource_group_name": rg_name,
                "subnet_name": subnet_name,
                "created_at": cluster.created_at,
                "cloud_provider_code": cluster.cloud_provider_code,
                "charge_type": cluster.charge_type,
                "cluster_version": cluster.cluster_version,
                "cluster_type": cluster.cluster_type,
                "created_by": user.get('username'),
                "region_id": cluster.region_id,
                "master_count": cluster.master_count,
                "master_instance_type": cluster.master_instance_type,
                "service_cidr": cluster.service_cidr,
                "tags": cluster.tags,
                "deletion_protection": cluster.deletion_protection,
                **resource_info,
            }
            result_items.append(item)
        return {
            "page": page,
            "page_size": page_size,
            "total": total,
            "items": result_items,
        }

        # 开启/关闭释放保护

    def toggle_server_release(self, instance_id: int):
        find = self.cluster_repo.toggle_cluster_release(instance_id)
        if not find:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return find

    # 释放
    def server_release(self, instance_id: int):
        with self.db.begin():
            instance = self.cluster_repo.get_by_id(instance_id)
            if not instance:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

            if instance.deletion_protection == 1:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="此集群无法释放")

            # active_status = {
            #     'SCALING',
            #     'UPGRADING',
            # }

            # if instance.status in active_status:
            #     raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前集群正在使用，无法释放")
            result = self.cluster_repo.cluster_release(instance_id)
            if not result:
                raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
            # -----------------------------
            # 5. VPC / 子网 / 公网 IP / 系统盘 / 数据盘 / 资源组绑定   RUNNING
            # -----------------------------
            if instance.vpc_id:
                self.vpc_service.update_vpc(instance.vpc_id, 'release')
            for subnet_id in instance.subnet_ids:
                self.subnet_service.update_subnet(subnet_id, 'release')
            return result

    # 节电池列表
    def cluster_pool_list(self, cluster_id: int):
        return self.node_pool_repo.cluster_pool_list(cluster_id)

    # 节点列表
    def cluster_node_list(self, cluster_id: int, pool_id: int = None):
        items = self.node_repo.cluster_node_list(cluster_id, pool_id)
        result_items = []
        for node, charge_type in items:
            resource_info = self.cluster_repo.get_cluster_resource_usage(node.cluster_id)
            item = {
                "id": node.id,
                "node_pool_id": node.node_pool_id,
                "cluster_id": node.cluster_id,
                "node_name": node.node_name,
                "created_at": node.created_at,
                "charge_type": charge_type,
                "private_ip": node.private_ip,
                "status": node.status,
                "cluster_node_role": node.cluster_node_role,
                "node_id": node.node_id,
                **resource_info,
            }
            result_items.append(item)
        return result_items
