from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.repositories.cmp.fs_mount_repo import FileMountRepository
from app.schemas.cmp.fs_mount_schema import FileSystemMountCreate, FileSystemMountOut, FileSystemMountPage

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

class FileMountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo: FileMountRepository = FileMountRepository(db)

    # 创建挂载点 cephfs/gpfs
    def fs_mount_create(self, user_id: int, data: FileSystemMountCreate):
        payload = {
            **data.model_dump(),
            "created_by": user_id,
            "mount_id": f"{data.fs_type}-{generate(size=12)}",
            "mount_name": f"{data.fs_type}-{generate(size=16)}",
            "instance_id": user_id,
        }
        result = self.repo.fs_mount_create(payload)
        return result


    # 分页列表
    def fs_mount_page_list(
        self,
        page: int,
        page_size: int,
        user_id: int,
        mount_type: str,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        mount_name: Optional[str] = None,
    ):
        if not user_id:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        items, total = self.repo.fs_mount_page_list(page, page_size, user_id, mount_type, provider_code, region_id, zone_id, mount_name)
        return FileSystemMountPage(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
        )