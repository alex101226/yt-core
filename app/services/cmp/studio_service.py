import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from nanoid import generate
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.cmp.studio_repo import StudioRepository
from app.repositories.sso.user_repo import UserRepository
from app.schemas.cmp.studio_schema import (
    StudioGpuUsageItemSchema,
    StudioListItemSchema,
    StudioMetricRingSchema,
    StudioNodeItemSchema,
    StudioNodePageSchema,
    StudioNodeTrendItemSchema,
    StudioNodeTrendSchema,
    StudioOptionSchema,
    StudioOverviewSchema,
    StudioPageSchema,
    StudioTrendSeriesSchema,
)


class StudioService:
    def __init__(self, sso_db: Session, cmp_db: Session):
        self.sso_db = sso_db
        self.cmp_db = cmp_db
        self.repo = StudioRepository(cmp_db)
        self.user_repo = UserRepository(sso_db)
        self.member_repo = MemberRepository(cmp_db)

    def _resolve_scope(self, current_user: dict) -> Optional[int]:
        user_id = current_user.get("user_id")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        if user.user_type == "internal":
            return None
        return user.id if (user.parent_id or 0) == 0 else user.parent_id

    def _ensure_accessible_studio(self, studio_id: int, current_user: dict):
        studio = self.repo.get_by_id(studio_id)
        if not studio:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        owner_user_id = self._resolve_scope(current_user)
        if owner_user_id is not None and studio.created_by != owner_user_id:
            raise BusinessException(code=ErrorCode.UNAUTHORIZED, message=Message.UNAUTHORIZED)
        return studio

    def _get_accessible_studios(self, current_user: dict):
        owner_user_id = self._resolve_scope(current_user)
        return self.repo.get_accessible_studios(owner_user_id)

    def _memory_total_gb(self, node) -> float:
        if node.cpu:
            return float(node.cpu * 2)
        if node.system_disk_size:
            return float(max(node.system_disk_size / 4, 4))
        return 0.0

    def _usage_snapshot(self, key: str, cpu_total: int, gpu_total: int, memory_total_gb: float):
        seed_key = f"{key}:{datetime.now(timezone.utc).strftime('%Y%m%d%H')}"
        rng = random.Random(seed_key)
        cpu_rate = round(rng.uniform(8, 58), 1) if cpu_total else 0.0
        gpu_rate = round(rng.uniform(0, 68), 1) if gpu_total else 0.0
        memory_rate = round(rng.uniform(18, 76), 1) if memory_total_gb else 0.0
        gpu_memory_total = 0.0
        gpu_memory_used = 0.0
        if gpu_total:
            gpu_memory_total = float(gpu_total * 4)
            gpu_memory_used = round(gpu_memory_total * gpu_rate / 100, 2)
        return {
            "cpu_usage_rate": cpu_rate,
            "gpu_usage_rate": gpu_rate,
            "memory_usage_rate": memory_rate,
            "gpu_memory_total": gpu_memory_total,
            "gpu_memory_used": gpu_memory_used,
        }

    def _aggregate_node_metrics(self, nodes: List):
        if not nodes:
            return {
                "cpu_usage_rate": 0.0,
                "gpu_usage_rate": 0.0,
                "memory_usage_rate": 0.0,
            }
        cpu_rates = []
        gpu_rates = []
        memory_rates = []
        for node in nodes:
            memory_total = self._memory_total_gb(node)
            snapshot = self._usage_snapshot(f"studio-node-{node.id}", node.cpu or 0, node.gpu_amount or 0, memory_total)
            cpu_rates.append(snapshot["cpu_usage_rate"])
            gpu_rates.append(snapshot["gpu_usage_rate"])
            memory_rates.append(snapshot["memory_usage_rate"])
        return {
            "cpu_usage_rate": round(sum(cpu_rates) / len(cpu_rates), 1) if cpu_rates else 0.0,
            "gpu_usage_rate": round(sum(gpu_rates) / len(gpu_rates), 1) if gpu_rates else 0.0,
            "memory_usage_rate": round(sum(memory_rates) / len(memory_rates), 1) if memory_rates else 0.0,
        }

    def _build_trend_labels(self):
        now = datetime.now(timezone.utc)
        return [
            (now - timedelta(minutes=6 * offset)).astimezone(timezone.utc).strftime("%H:%M")
            for offset in range(9, -1, -1)
        ]

    def _build_studio_monitor(self, studio_id: int):
        labels = self._build_trend_labels()
        cpu_rates = []
        gpu_rates = []
        memory_rates = []
        for index, label in enumerate(labels):
            rng = random.Random(f"studio-monitor:{studio_id}:{label}:{index}")
            cpu_rates.append(round(rng.uniform(10, 60), 1))
            gpu_rates.append(round(rng.uniform(0, 65), 1))
            memory_rates.append(round(rng.uniform(20, 80), 1))
        return StudioTrendSeriesSchema(
            labels=labels,
            cpu_usage_rate=cpu_rates,
            gpu_usage_rate=gpu_rates,
            memory_usage_rate=memory_rates,
        )

    def _build_node_monitor(self, nodes: List):
        labels = self._build_trend_labels()
        items = []
        for node in nodes:
            cpu_rates = []
            gpu_rates = []
            memory_rates = []
            for index, label in enumerate(labels):
                rng = random.Random(f"node-monitor:{node.id}:{label}:{index}")
                cpu_rates.append(round(rng.uniform(10, 55), 1))
                gpu_rates.append(round(rng.uniform(0, 70), 1) if (node.gpu_amount or 0) > 0 else 0.0)
                memory_rates.append(round(rng.uniform(18, 78), 1))
            items.append(
                StudioNodeTrendItemSchema(
                    node_id=node.id,
                    node_name=node.node_name,
                    cpu_usage_rate=cpu_rates,
                    gpu_usage_rate=gpu_rates,
                    memory_usage_rate=memory_rates,
                )
            )
        return StudioNodeTrendSchema(labels=labels, items=items)

    def _resolve_member_id(self, operator: dict) -> Optional[int]:
        user_id = operator.get("user_id")
        parent_id = operator.get("parent_id") or 0
        owner_user_id = user_id if parent_id == 0 else parent_id
        member = self.member_repo.get_by_user_id(owner_user_id)
        return member.id if member else None

    def create_from_cluster(self, operator: dict, cluster):
        existed = self.repo.get_by_cluster_id(cluster.id)
        if existed:
            return existed
        payload = {
            "cluster_id": cluster.id,
            "studio_name": cluster.cluster_name,
            "instance_id": generate(size=8),
            "studio_type": "基础版",
            "member_id": self._resolve_member_id(operator),
            "resource_group_id": cluster.resource_group_id,
            "status": "ENABLED",
            "enabled": True,
            "created_by": operator.get("user_id"),
            "created_by_name": operator.get("username"),
        }
        return self.repo.create(payload)

    def page_list(self, current_user: dict, page: int, page_size: int, studio_name: Optional[str] = None):
        owner_user_id = self._resolve_scope(current_user)
        items, total = self.repo.studio_page_list(owner_user_id, page, page_size, studio_name)
        result_items = []
        for studio, cluster, resource_group_name in items:
            nodes, _ = self.repo.studio_node_page_list(owner_user_id, studio.id, 1, 1000)
            node_objs = [node for node, _, _, _, _ in nodes]
            node_stats = self.repo.get_node_stats(cluster.id)
            metrics = self._aggregate_node_metrics(node_objs)
            result_items.append(
                StudioListItemSchema(
                    id=studio.id,
                    studio_name=studio.studio_name,
                    instance_id=studio.instance_id,
                    studio_type=studio.studio_type,
                    resource_group_name=resource_group_name,
                    creator_name=studio.created_by_name,
                    region_display=f"{cluster.region_id}/{cluster.zone_id}",
                    kubernetes_version=cluster.cluster_version,
                    created_at=studio.created_at,
                    gpu_count=node_stats["gpu_total"],
                    cpu_usage_rate=metrics["cpu_usage_rate"],
                    gpu_usage_rate=metrics["gpu_usage_rate"],
                    memory_usage_rate=metrics["memory_usage_rate"],
                    healthy_node_count=node_stats["healthy_nodes"],
                    total_node_count=node_stats["total_nodes"],
                    enabled=studio.enabled,
                    status=studio.status,
                )
            )
        return StudioPageSchema(page=page, page_size=page_size, total=total, items=result_items)

    def studio_list(self, current_user: dict):
        owner_user_id = self._resolve_scope(current_user)
        rows = self.repo.studio_list(owner_user_id)
        return [StudioOptionSchema(id=row.id, studio_name=row.studio_name) for row in rows]

    def overview(self, current_user: dict, studio_id: Optional[int] = None):
        # 资源总览页始终按当前权限范围内全部 Studio 聚合统计。
        # studio_id 参数仅为兼容前端已传值场景，当前不参与过滤。
        studio_pairs = self._get_accessible_studios(current_user)

        all_nodes = []
        studio_count = 0
        healthy_total = 0
        node_total = 0
        gpu_usages = []
        for studio_item, cluster in studio_pairs:
            studio_count += 1
            cluster_id = studio_item.cluster_id if hasattr(studio_item, "cluster_id") else studio.cluster_id
            rows, _ = self.repo.studio_node_page_list(self._resolve_scope(current_user), studio_item.id, 1, 1000)
            nodes = [node for node, _, _, _, _ in rows]
            all_nodes.extend(nodes)
            node_stats = self.repo.get_node_stats(cluster_id)
            healthy_total += node_stats["healthy_nodes"]
            node_total += node_stats["total_nodes"]
            for node in nodes:
                memory_total = self._memory_total_gb(node)
                snapshot = self._usage_snapshot(f"studio-node-{node.id}", node.cpu or 0, node.gpu_amount or 0, memory_total)
                if (node.gpu_amount or 0) <= 0:
                    continue
                gpu_usages.append(
                    StudioGpuUsageItemSchema(
                        studio_name=studio_item.studio_name,
                        node_name=node.node_name,
                        gpu_status="[空闲]" if snapshot["gpu_usage_rate"] < 50 else "[使用中]",
                        gpu_model=node.gpu_spec,
                        gpu_count=node.gpu_amount or 0,
                        gpu_memory_total=snapshot["gpu_memory_total"],
                        gpu_memory_used=snapshot["gpu_memory_used"],
                    )
                )
        metrics = self._aggregate_node_metrics(all_nodes)
        return StudioOverviewSchema(
            studio_count=studio_count,
            studio_normal_text=f"{studio_count}/{studio_count}" if studio_count else "0/0",
            node_normal_text=f"{healthy_total}/{node_total}",
            metrics=StudioMetricRingSchema(**metrics),
            studio_monitor=self._build_studio_monitor(studio_id or 0),
            node_monitor=self._build_node_monitor(all_nodes),
            gpu_usages=gpu_usages,
        )

    def node_page_list(
        self,
        current_user: dict,
        studio_id: Optional[int],
        page: int,
        page_size: int,
        node_name: Optional[str] = None,
    ):
        owner_user_id = self._resolve_scope(current_user)
        if studio_id is not None:
            self._ensure_accessible_studio(studio_id, current_user)
        rows, total = self.repo.studio_node_page_list(owner_user_id, studio_id, page, page_size, node_name)
        items = []
        for node, row_studio_id, studio_name, charge_type, node_type in rows:
            memory_total = self._memory_total_gb(node)
            snapshot = self._usage_snapshot(f"studio-node-{node.id}", node.cpu or 0, node.gpu_amount or 0, memory_total)
            gpu_display = "-"
            if (node.gpu_amount or 0) > 0:
                gpu_display = f"{node.gpu_amount} × {node.gpu_spec or '-'} {node.gpu_memory or 0}GB"
            items.append(
                StudioNodeItemSchema(
                    id=node.id,
                    studio_id=row_studio_id,
                    node_name=node.node_name,
                    studio_name=studio_name,
                    spec=node.instance_type_id,
                    node_type="云服务器" if (node_type or "").lower() == "ecs" else "裸金属",
                    status="正常" if node.status == "RUNNING" else node.status,
                    private_ip=node.private_ip,
                    vcpu_total=int(node.cpu or 0),
                    vcpu_usage_rate=snapshot["cpu_usage_rate"],
                    memory_total_gb=memory_total,
                    memory_usage_rate=snapshot["memory_usage_rate"],
                    gpu_display=gpu_display,
                    charge_type="按量付费" if charge_type == "PostPaid" else ("包年包月" if charge_type == "PrePaid" else "-"),
                    created_by_name=node.created_by_name,
                    created_at=node.created_at,
                )
            )
        return StudioNodePageSchema(page=page, page_size=page_size, total=total, items=items)
