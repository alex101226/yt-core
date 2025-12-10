from typing import Optional

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.image_repository import ImageRepository

class ContainerImageRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建镜像服务
    def image_create(self, data: dict) -> bool:
        item = ImageRepository(**data)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return True

    # 列表
    def con_image_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[str] = None,
            resource_group_id: Optional[int] = None,
            repository_name: str = None
    ):
        query = self.db.query(
            ImageRepository.id,
            ImageRepository.repository_id,
            ImageRepository.repository_name,
            ImageRepository.cloud_provider_code,
            ImageRepository.region_id,
            ImageRepository.resource_group_id,
            ImageRepository.description,
            ImageRepository.namespace_count,
            ImageRepository.capacity_gb,
            ImageRepository.used_capacity_gb,
            ImageRepository.status,
            ImageRepository.charge_type,
            ImageRepository.created_by,
            ImageRepository.created_at,
            ImageRepository.updated_at
        )
        filters = [ImageRepository.created_by == user_id]
        if provider_code:
            filters.append(ImageRepository.cloud_provider_code == provider_code)
        if region_id:
            filters.append(ImageRepository.region_id == region_id)
        if resource_group_id:
            filters.append(ImageRepository.resource_group_id == resource_group_id)
        if repository_name:
            filters.append(ImageRepository.repository_name.like(f"%{repository_name}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(ImageRepository.id.desc()).offset(offset_value).limit(page_size).all()
        logger.info(f'这是 {items}')
        return items, total