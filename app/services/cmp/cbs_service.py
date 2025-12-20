from typing import List, Optional
from sqlalchemy.orm import Session
from nanoid import generate

from app.repositories.cmp.cbs_repo import CbsDiskRepository
from app.schemas.cmp.cbs_disk_schema import CbsDiskBase, CbsDiskCreate, CbsDiskOut, CbsDiskPage

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message


class CbsService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CbsDiskRepository(db)


    #   创建硬盘
    def cbs_create_s(self, user_id: int, data: CbsDiskCreate):
        payload = {
            **data.model_dump(),
            "user_id": user_id,
            "disk_id": f"CBS-{generate(size=12)}",
            "encrypted": False,
            # "status": data.attached_instance_id if data.status == "InUse" else "Available",
            "status": "InUse" if data.attached_instance_id else "Available",
            "attached_time": data.attached_time if data.attached_time  else None,
        }
        result = self.repo.cbs_create(payload)
        return result

    # 返回分页列表
    def cbs_page_list(
        self,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[int] = None,
        zone_id: Optional[int] = None,
        resource_group_id: Optional[int] = None,
        cbs_id: Optional[str] = None
    ) -> CbsDiskPage:
        items, total = self.repo.get_page_list(page, page_size, provider_code, region_id, zone_id, resource_group_id, cbs_id)
        item_out = [CbsDiskOut.model_validate(s) for s in items]
        return CbsDiskPage(
            total=total,
            page=page,
            page_size=page_size,
            items=item_out,
        )


    # 释放
    def cbs_release(self, cbs_id: int) -> bool:
        db_cbs = self.repo.get_find(cbs_id)
        if db_cbs is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        invalid = {'Creating', 'Attaching', 'Detaching'}
        if db_cbs.status in invalid:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="请先卸载实例后再执行释放操作")

        return self.repo.cbs_release(cbs_id)

    # 卸载
    def cbs_uninstall(self, cbs_id: int) -> bool:
        db_cbs = self.repo.get_find(cbs_id)
        if db_cbs is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if db_cbs.disk_type == 'system':
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="系统盘不允许卸载实例")

        # if db_cbs.user_id != user_id:
        #     raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message="用户错误")
        return self.repo.cbs_uninstall(cbs_id)