from sqlalchemy.orm import Session
from typing import Optional
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.repositories.cmp.cephfs_file_repo import CephfsFileRepository
from app.repositories.cmp.gpfs_repo import GPFSRepository

from app.repositories.cmp.fs_mount_repo import FileMountRepository
from app.schemas.cmp.fs_mount_schema import FileSystemMountCreate, FileSystemMountPage

class FileMountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo: FileMountRepository = FileMountRepository(db)
        self.gpfs_repo: GPFSRepository = GPFSRepository(db)
        self.cephfs_repo = CephfsFileRepository(db)

    # 创建挂载点 cephfs/gpfs
    def fs_mount_create(self, user_id: int, data: FileSystemMountCreate):
        payload = {
            **data.model_dump(),
            "created_by": user_id,
            "mount_id": f"{data.fs_type}-{generate(size=12)}",
            "mount_name": f"{data.fs_type}-{generate(size=16)}",
            "instance_id": user_id,
            "status": "MOUNTED",
        }
        result = self.repo.fs_mount_create(payload)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        self.save_file_data(data.fs_type, data.fs_id, True)

        self.db.commit()
        self.db.refresh(result)
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

    # 卸载
    def uninstall(self, mount_id: int):
        result = self.repo.uninstall(mount_id)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        self.save_file_data(result.fs_type, result.fs_id, False)

        self.db.commit()
        self.db.refresh(result)
        return result

    # 释放
    def release(self, mount_id: int):
        result = self.repo.release(mount_id)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)

        active_status = {
            'MOUNTING', 'MOUNTED'
        }

        if result.status in active_status:
            raise BusinessException(code=ErrorCode.FAILED, message= "挂载中的节点不允许释放")
        return result


    # 更新文件系统数据
    def save_file_data(self, fs_type: str, fs_id: int, is_mounted: bool):
        status = 'MOUNTED' if is_mounted else 'ACTIVE'

        if fs_type == "cephfs":
            self.cephfs_repo.save_status(fs_id, status)
        else:
            self.gpfs_repo.save_status(fs_id, status)