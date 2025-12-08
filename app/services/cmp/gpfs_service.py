from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.repositories.cmp.gpfs_repo import GPFSRepository
from app.schemas.cmp.gpfs_schema import GPFSCreate, GPFSOut, GPFSPage

class GPFSService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = GPFSRepository(db)

    # 创建gpfs
    def gpfs_create(self, user_id: int, data: GPFSCreate):
        payload = {
            **data.model_dump(),
            "created_by": user_id,
            "status": "ACTIVE",
            "fs_id": f"{data.storage_type}-{generate(size=12)}",
            "fs_name": f"{data.storage_type}-{generate(size=16)}",
        }
        result = self.repo.gpfs_create(payload)
        return result

# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3LCJleHAiOjE3NjUxNjU5MjMsInR5cGUiOiJhY2Nlc3MifQ.u3u-TJQNWSFJ23Tn0OM85CyLDUqoNoaRLaxlIHoBKkc
    # 分页列表
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
    ) -> Optional[GPFSPage]:
        items, total = self.repo.gpfs_page_list(
            user_id, page, page_size, provider_code, region_id, zone_id,
            storage_type, fs_name
        )
        return GPFSPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[GPFSOut.model_validate(i) for i in items]
        )