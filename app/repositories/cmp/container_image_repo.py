from tkinter import Image
from typing import Optional

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.image_repository import ImageRepository

from app.models.cmp.resource_group import ResourceGroup

class ContainerImageRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建镜像服务
    def image_create(self, data: dict) -> bool:
        item = ImageRepository(**data)
        self.db.add(item)
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(item)
        return item

    # 列表
    def con_image_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
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
            ImageRepository.updated_at,
            ResourceGroup.rg_name.label('resource_group_name'),
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == ImageRepository.resource_group_id
        )
        filters = [ImageRepository.created_by == user_id, ImageRepository.is_released == 0]
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
        return items, total

    def get_by_id(self, image_id: int) -> Optional[Image]:
        return self.db.query(ImageRepository).filter(ImageRepository.id == image_id).first()

    # 停止容器
    def release(self, image_id: int):
        find = self.get_by_id(image_id)
        if not find:
            return None
        find.status = 'RELEASED'
        find.is_released = 1
        self.db.commit()
        self.db.refresh(find)
        return find

