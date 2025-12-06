from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.schemas.cmp.oss_schema import OssCreate, OssPage, OssOut
from app.repositories.cmp.oss_repo import OssRepoRepository

class OssBucketService:
    def __init__(self, db: Session):
        self.db = db
        self.oss_repo = OssRepoRepository(db)

    def oss_create(self, user_id: int, data: OssCreate):
        payload = {
            **data.model_dump(),
            "user_id": user_id,
            "charge_type": "PostPaid",
            "status": "ACTIVE",
            "bucket_id": f"oss-{generate(size=12)}",
            "endpoint": "ecs.aliyuncs.com"
        }
        result = self.oss_repo.oss_create(payload)
        return result

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
        items, total = self.oss_repo.oss_page_list(page, page_size, provider_code, region_id, resource_group_id, bucket_name, permission)
        return OssPage(
            total=total,
            page=page,
            page_size=page_size,
            items = [OssOut.model_validate(item) for item in items]
        )