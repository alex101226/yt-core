from typing import Optional

from sqlalchemy.orm import Session

from app.models.cmp import ResourceGroup
from app.models.cmp.cloud_image import CloudImage

class CloudImageRepo:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> CloudImage:
        """
        创建云镜像记录
        """
        cloud_image = CloudImage(**data)
        self.db.add(cloud_image)
        self.db.flush()
        # self.session.commit()
        # self.session.refresh(cloud_image)
        return cloud_image

    #   查询云镜像分页列表
    def get_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        image_name: Optional[str] = None,
    ):
        query = self.db.query(
            CloudImage,
            ResourceGroup.rg_name.label("resource_group_name")
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == CloudImage.resource_group_id
        ).order_by(CloudImage.id.desc())

        # 必传过滤条件
        filters = [CloudImage.created_by == user_id, CloudImage.is_released == 0]

        # 可选条件
        if cloud_provider_code:
            filters.append(CloudImage.cloud_provider_code == cloud_provider_code)
        if region_id:
            filters.append(CloudImage.region_id == region_id)
        if resource_group_id:
            filters.append(CloudImage.resource_group_id == resource_group_id)
        if image_name:
            filters.append(CloudImage.image_name.like(f"%{image_name}%"))

        if filters:
            query = query.filter(*filters)

        # 总数
        total = query.count()

        # 分页
        offset_value = (page - 1) * page_size
        items = query.offset(offset_value).limit(page_size).all()

        return items, total