from typing import Optional

from sqlalchemy.orm import Session

from app.models.cmp import CephfsFile
from app.core.logger import logger
from app.schemas.cmp.cephfs_file_schema import CephfsBase, CephfsCreate


class CephfsFileRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建
    def cephfs_file_create(self, data: dict):
        item = CephfsFile(**data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return True

    # 返回cephfs的列表
    def cephfs_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[str] = None,
            resource_group_id: Optional[int] = None,
            storage_type: str = None,
            fs_name: str = None
    ):
        query = self.db.query(
            CephfsFile.id,
            CephfsFile.fs_name,
            CephfsFile.cloud_provider_code,
            CephfsFile.region_id,
            CephfsFile.resource_group_id,
            CephfsFile.description,
            CephfsFile.storage_type,
            CephfsFile.capacity_gb,
            # CephfsFile.used_size_gb,
            CephfsFile.price,
            CephfsFile.status,
            CephfsFile.charge_type,
            CephfsFile.fs_id,
            CephfsFile.user_id,
            CephfsFile.created_at,
            CephfsFile.updated_at
        )
        filters = [CephfsFile.user_id == user_id]
        if provider_code:
            filters.append(CephfsFile.cloud_provider_code == provider_code)
        if region_id:
            filters.append(CephfsFile.region_id == region_id)
        if resource_group_id:
            filters.append(CephfsFile.resource_group_id == resource_group_id)
        if storage_type:
            filters.append(CephfsFile.storage_type == storage_type)
        if fs_name:
            filters.append(CephfsFile.fs_name.like(f"%{fs_name}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(CephfsFile.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total