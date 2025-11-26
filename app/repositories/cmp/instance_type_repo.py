# app/repositories/cmp/instance_type_repo.py
from sqlalchemy import not_, func
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from app.models.cmp.instance_type import InstanceType


class InstanceTypeRepo:
    def __init__(self, db: Session):
        self.db = db

    #   批量插入或更新可用区数据
    def bulk_upsert(self, provider_code: str, instances: List[dict]):

        now = datetime.now()

        updatable_fields = [
            "instance_family",
            "generation",
            "cpu_core_count",
            "memory_size",
            "architecture",
            "gpu_amount",
            "gpu_spec",
            "gpu_memory",
            "local_storage_amount",
            "local_storage_capacity",
            "network_performance",
            "is_io_optimized",
            "price",
        ]

        for i in instances:
            existing = (
                self.db.query(InstanceType)
                .filter(
                    InstanceType.cloud_provider_code == provider_code,
                    InstanceType.instance_type_id == i["instance_type_id"],
                )
                .first()
            )
            if existing:
                for field in updatable_fields:
                    setattr(existing, field, i.get(field))
                existing.updated_at = now
            else:
                i["cloud_provider_code"] = provider_code
                self.db.add(InstanceType(**i))
        self.db.commit()


    def get_by_instance_type(self, provider_code: str) -> list[type[InstanceType]]:
        return self.db.query(InstanceType).filter_by(cloud_provider_code = provider_code).all()

    #   generation
    # "cpu_core_count": inst.cpu_core_count,
    # "gpu_amount": inst.gpu_amount,
    # "gpu_spec": inst.gpu_spec,
    # "gpu_memory": inst.gpu_memory,
    # "zone_id": search.zone_id,
    # "architecture": inst.architecture,
    # "memory_size": inst.memory_size,
    def get_by_instance_type_find(self, instance_type_id: str) -> Optional[type[InstanceType]]:
        return self.db.query(InstanceType).filter(
            InstanceType.instance_type_id==instance_type_id
        ).first()

    #   批量查找全量规格
    def batch_fetch_instance_types_from_db(self, instance_type_ids: List[str]) -> dict[Any, type[InstanceType]]:
        """一次性从 DB 查询所有 instance types，并返回 id->model 映射"""
        if not instance_type_ids:
            return {}
        rows = (
            self.db.query(InstanceType)
            .filter(InstanceType.instance_type_id.in_(instance_type_ids))
            .all()
        )
        return {r.instance_type_id: r for r in rows}