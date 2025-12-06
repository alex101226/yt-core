from typing import Optional

from sqlalchemy.orm import Session

from app.models.cmp.oss import OssBucket

class OssRepoRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建oss
    def oss_create(self, data: dict) -> bool:
        bucket = OssBucket(**data)
        self.db.add(bucket)
        self.db.commit()
        self.db.refresh(bucket)
        return True

    def oss_find(self, oss_id: int):
        return self.db.query(OssBucket).filter_by(id = oss_id).first()

    # 返回oss的列表
    def oss_page_list(
        self,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[int] = None,
        resource_group_id: Optional[int] = None,
        bucket_name: str = None,
        permission: str = None
    ):
        query = self.db.query(
            OssBucket.id,
            OssBucket.bucket_name,
            OssBucket.cloud_provider_code,
            OssBucket.region_id,
            OssBucket.resource_group_id,
            OssBucket.description,
            OssBucket.storage_class,
            OssBucket.permission,
            OssBucket.bucket_id,
            OssBucket.status,
            OssBucket.charge_type,
            OssBucket.used_size_bytes,
            OssBucket.user_id,
            OssBucket.created_at,
            OssBucket.updated_at
        )
        filters = []
        if provider_code is not None:
            filters.append(OssBucket.cloud_provider_code == provider_code)
        if region_id is not None:
            filters.append(OssBucket.region_id == region_id)
        if resource_group_id is not None:
            filters.append(OssBucket.resource_group_id == resource_group_id)
        if bucket_name is not None:
            filters.append(OssBucket.bucket_name.like(f"%{bucket_name}%"))
        if permission is not None:
            filters.append(OssBucket.permission == permission)

        if filters:
            query = query.filter(*filters)
        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(OssBucket.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total
