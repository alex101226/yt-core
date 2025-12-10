from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.repositories.cmp.container_image_repo import ContainerImageRepository
from app.schemas.cmp.container_image_schema import ContainerImageCreate, ContainerImagePage, ContainerImageOut

class ContainerImageService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ContainerImageRepository(db)


    # 创建镜像服务
    def image_create(self, user_id: int, data: ContainerImageCreate):
        payload = {
            **data.model_dump(),
            "created_by": user_id,
            "enable_https": 0,
            "repository_id": f"cr-{generate(size=12)}",
        }
        result = self.repo.image_create(payload)
        return result


    # 分页列表
    def con_image_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[int] = None,
            resource_group_id: Optional[int] = None,
            repository_name: str = None
    ):
        items, total = self.repo.con_image_page_list(
            user_id, page, page_size, provider_code, region_id, resource_group_id,
            repository_name
        )

        return ContainerImagePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[ContainerImageOut.model_validate(item) for item in items]
        )