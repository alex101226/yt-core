from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cmp import CephfsFile, ResourceGroup

class CephfsFileRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建
    def cephfs_file_create(self, data: dict):
        item = CephfsFile(**data)
        self.db.add(item)
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(item)
        return item

    # 返回cephfs的列表
    def cephfs_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
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
            # 👇 关键：随机 used_capacity_gb（0 ~ capacity_gb-1）
            func.floor(func.rand() * CephfsFile.capacity_gb).label("used_size_gb"),
            CephfsFile.capacity_gb,
            # CephfsFile.used_size_gb,
            # CephfsFile.price,
            CephfsFile.status,
            CephfsFile.charge_type,
            CephfsFile.fs_id,
            # CephfsFile.user_id,
            CephfsFile.created_at,
            CephfsFile.updated_at,
            ResourceGroup.rg_name.label('resource_group_name'),
        ).outerjoin(
            ResourceGroup, ResourceGroup.id == CephfsFile.resource_group_id
        ).order_by(CephfsFile.id.desc())
        filters = [CephfsFile.created_by == user_id, CephfsFile.is_released==0]
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

    # 下拉列表接口
    def cephfs_list(self, user_id: int, region_id: str, status: str = None):
        query = self.db.query(
            CephfsFile.id,
            CephfsFile.fs_name,
            CephfsFile.capacity_gb,
            # CephfsFile.price,
            CephfsFile.status,
        )
        filters = [
            CephfsFile.is_released == 0,
            CephfsFile.region_id == region_id,
            CephfsFile.created_by == user_id,
            CephfsFile.status == 'ACTIVE'
        ]

        if filters:
            query = query.filter(*filters)

        rows = query.order_by(CephfsFile.id.desc()).all()
        if not rows:
            return None
        return [
            {
                "id": row.id,
                "fs_name": row.fs_name,
                "capacity_gb": row.capacity_gb,
                "status": row.status,
            }
            for row in rows
        ]

    # 查询
    def get_by_id(self, cephfs_id: int) -> Optional[dict]:
        row = self.db.query(CephfsFile).filter(CephfsFile.id == cephfs_id).first()
        return row

     # 容量配置
    def save_capacity_gb(self, data: dict):
        cephfs_id = data.get("cephfs_id")
        find = self.get_by_id(cephfs_id)
        if not find:
            return None
        find.capacity_gb = data.get("capacity_gb")
        self.db.commit()
        self.db.refresh(find)
        return True

        # 释放    实例状态：字典表=FS_STATUS

    def release(self, cephfs_id: int):
        find = self.get_by_id(cephfs_id)
        if not find:
            return None
        find.status = 'DELETING'
        find.is_released = 1
        self.db.commit()
        self.db.refresh(find)
        return True

    # 修改状态  fs_type
    def save_status(self, cephfs_id: int, status: str):
        find = self.get_by_id(cephfs_id)
        if not find:
            return None
        find.status = status
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(find)
        return True