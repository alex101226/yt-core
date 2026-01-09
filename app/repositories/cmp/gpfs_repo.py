from typing import Optional

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.core.logger import logger
from app.models.cmp.gpfs_file import GPFSFile


class GPFSRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建gpfs
    def gpfs_create(self, data: dict) -> bool:
        item = GPFSFile(**data)
        self.db.add(item)
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(item)
        return item

    # 返回gpfs的列表
    def gpfs_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[str] = None,
            zone_id: Optional[str] = None,
            storage_type: str = None,
            fs_name: str = None
    ):
        query = self.db.query(
            GPFSFile.id,
            GPFSFile.fs_id,
            GPFSFile.fs_name,
            GPFSFile.fs_alias,
            GPFSFile.description,
            GPFSFile.cloud_provider_code,
            GPFSFile.region_id,
            GPFSFile.zone_id,
            GPFSFile.resource_group_id,
            GPFSFile.vpc_id,
            GPFSFile.subnet_id,
            GPFSFile.storage_type,
            GPFSFile.capacity_gb,
            GPFSFile.used_capacity_gb,
            GPFSFile.price,
            GPFSFile.status,
            GPFSFile.charge_type,
            GPFSFile.created_by,
            GPFSFile.created_at,
            GPFSFile.updated_at
        )

        filters = [GPFSFile.created_by == user_id, GPFSFile.is_released == 0]
        if provider_code:
            filters.append(GPFSFile.cloud_provider_code == provider_code)
        if region_id:
            filters.append(GPFSFile.region_id == region_id)
        if zone_id:
            filters.append(GPFSFile.zone_id == zone_id)
        if storage_type:
            filters.append(GPFSFile.storage_type == storage_type)
        if fs_name:
            filters.append(GPFSFile.fs_name.like(f"%{fs_name}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(GPFSFile.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total


    # 下拉列表接口
    def gpfs_list(self, user_id: int, subnet_id: str):
        rows = self.db.query(
            GPFSFile.id,
            GPFSFile.fs_name,
        ).filter(
            GPFSFile.is_released == 0,
            GPFSFile.subnet_id == subnet_id,
            GPFSFile.created_by == user_id,
        ).order_by(GPFSFile.id.desc()).all()
        if not rows:
            return None
        return [
            {
                "id": row.id,
                "fs_name": row.fs_name,
            }
            for row in rows
        ]
