from typing import Optional, List
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.fs_mount_point import FileSystemMount
from app.schemas.cmp.fs_mount_schema import FileSystemMountCreate, FileSystemMountPage

class FileMountRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建挂载点 cephfs/gpfs
    def fs_mount_create(self, data: dict) -> bool:
        mount = FileSystemMount(**data)
        self.db.add(mount)
        self.db.commit()
        self.db.refresh(mount)
        return True


    def fs_mount_page_list(
        self,
        page: int,
        page_size: int,
        user_id: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        mount_name: Optional[str] = None,
    ):

        if user_id is None:
            return None

        query = self.db.query(
            FileSystemMount.id,
            FileSystemMount.mount_id,
            FileSystemMount.mount_alias,
            FileSystemMount.mount_name,
            FileSystemMount.domain_name,
            FileSystemMount.security_group_id,
            FileSystemMount.status,
            FileSystemMount.cloud_provider_code,
            FileSystemMount.region_id,
            FileSystemMount.zone_id,
            FileSystemMount.instance_id,
            FileSystemMount.vpc_id,
            FileSystemMount.subnet_id,
            FileSystemMount.fs_type,
            FileSystemMount.fs_id,
            FileSystemMount.created_at,
            FileSystemMount.updated_at,
        )

        filters = [FileSystemMount.created_by == user_id]
        if provider_code is not None:
            filters.append(FileSystemMount.cloud_provider_code == provider_code)
        if region_id is not None:
            filters.append(FileSystemMount.region_id == region_id)
        if zone_id is not None:
            filters.append(FileSystemMount.zone_id == zone_id)
        if mount_name is not None:
            filters.append(FileSystemMount.mount_name.like(f"%{mount_name}%"))

        if filters:
            query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(FileSystemMount.id.desc()).offset(offset_value).limit(page_size).all()
        logger.info(f'看下 {items}')
        return items, total