import json
from datetime import datetime, timezone

from sqlalchemy import func, or_

from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.cmp.cbs_disk import CbsDisk
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate


class CbsDiskRepository:
    def __init__(self, db: Session):
        self.db = db

    def cbs_create(self, data: dict) -> bool:
        disk = CbsDisk(**data)
        self.db.add(disk)
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(disk)
        return True

    def get_find(self, disk_id: int):
        return self.db.query(CbsDisk).filter(CbsDisk.id == disk_id, CbsDisk.is_released == 0).first()

    def get_page_list(
        self,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        resource_group_id: Optional[int] = None,
        cbs_id: Optional[str] = None,
    ):
        query = self.db.query(
            CbsDisk.id,
            CbsDisk.created_at,
            CbsDisk.updated_at,
            CbsDisk.disk_id,
            CbsDisk.cloud_provider_code,
            CbsDisk.region_id,
            CbsDisk.zone_id,
            CbsDisk.resource_group_id,
            CbsDisk.disk_type,
            CbsDisk.disk_category,
            CbsDisk.disk_size,
            CbsDisk.iops_level,
            CbsDisk.encrypted,
            CbsDisk.encryption_key_id,
            CbsDisk.charge_type,
            CbsDisk.period,
            CbsDisk.expired_time,
            CbsDisk.auto_renew,
            CbsDisk.attached_instance_id,
            CbsDisk.attached_device,
            CbsDisk.attached_time,
            CbsDisk.detached_time,
            CbsDisk.snapshot_count,
            CbsDisk.last_snapshot_time,
            CbsDisk.tags,
            CbsDisk.description,
        )
        filters = []
        if provider_code is not None:
            filters.append(CbsDisk.cloud_provider_code == provider_code)
        if region_id is not None:
            filters.append(CbsDisk.region_id == region_id)
        if zone_id is not None:
            filters.append(CbsDisk.zone_id == zone_id)
        if resource_group_id is not None:
            filters.append(CbsDisk.resource_group_id == resource_group_id)
        if cbs_id is not None:
            filters.append(CbsDisk.cbs_id.like(f"%{cbs_id}%"))
        # if tags:
        #     tag_filters = [
        #         func.json_contains(CbsDisk.tags, json.dumps([{"title": tag["title"]}]))
        #         for tag in tags
        #     ]
        #     filters.append(or_(*tag_filters))

        if filters:
            query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(CbsDisk.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total

    # 释放
    def cbs_release(self, cbs_id: int):
        db_obj = self.get_find(cbs_id)
        if db_obj is None:
            return None
        db_obj.is_released = 1
        self.db.commit()
        self.db.refresh(db_obj)
        return True

    # 卸载
    def cbs_uninstall(self, cbs_id: int):
        db_obj = self.get_find(cbs_id)
        if db_obj is None:
            return None
        # 1) 状态改为 AVAILABLE
        db_obj.status = 'AVAILABLE'

        # 2) 清除挂载关联
        db_obj.attached_instance_id = None
        db_obj.attached_device = None
        db_obj.detached_time = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(db_obj)
        return True