from typing import List, Optional
from sqlalchemy.orm import Session

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPOut, EIPPage

from app.repositories.cmp.eip_repo import EipRepository

class EIPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EipRepository(db)

    # 创建eip
    def create_eip(self, user_id: int, data: EIPCreate):
        result = self.repo.create_eip(user_id, data)
        return result

    # eip分页列表
    def get_eip_page_list(
        self,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        eip_id: Optional[str] = None,
        public_ip: Optional[str] = None
    ):
        items, total = self.repo.eip_page_list(
            page, page_size, provider_code, region_id, zone_id, resource_group_id, eip_id, public_ip
        )
        item_out = [EIPOut.model_validate(s) for s in items]
        return EIPPage(
            total=total,
            page=page,
            page_size=page_size,
            items = item_out
        )


    # eip解绑，绑定，释放
    def eip_action(self, status: str, eip_id: int, user_id: int):
        eip_find = self.repo.get_eip_by_id(eip_id)
        if eip_find is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if eip_find.status == 'ALLOCATING' or eip_find.status == 'BINDING':
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前eip状态不支持操作")

        if eip_find.user_id != user_id:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message="用户错误")

        result = self.repo.eip_action(status, eip_id)

        # logger.info(f'来到这里 {result}')
        return result