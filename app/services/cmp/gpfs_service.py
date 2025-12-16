from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

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


    # 返回gpfs的列表
    def gpfs_list(self, user_id: int, subnet_id: str):
        result = self.repo.gpfs_list(user_id, subnet_id)
        # logger.info(f'查看列表呗 {result}')
        if not result:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )
        return result