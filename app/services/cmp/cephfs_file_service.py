from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.repositories.cmp.cephfs_file_repo import CephfsFileRepository
from app.schemas.cmp.cephfs_file_schema import CephfsCreate, CephfsPage, CephfsOut

class CephfsFileService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CephfsFileRepository(db)

    def cephfs_file_create(self, user_id: int, data: CephfsCreate):
        payload = {
            **data.model_dump(),
            "user_id": user_id,
            "charge_type": "PostPaid",
            "status": "ACTIVE",
            "fs_id": f"cephfs-{generate(size=12)}",
        }
        result = self.repo.cephfs_file_create(payload)
        return result

    def oss_page_list(
            self,
            page: int,
            page_size: int,
            provider_code: Optional[str] = None,
            region_id: Optional[int] = None,
            resource_group_id: Optional[int] = None,
            storage_type: str = None,
            fs_name: str = None
    ):
        items, total = self.repo.cephfs_page_list(
            page, page_size, provider_code, region_id, resource_group_id,
            storage_type, fs_name
        )

        return CephfsPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[CephfsOut.model_validate(item) for item in items]
        )