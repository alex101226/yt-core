from typing import List, Optional
from sqlalchemy.orm import Session
from nanoid import generate

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException
from app.common.ipaddress import create_public_ip

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPOut, EIPPage, EIPSave
from app.repositories.cmp.eip_repo import EipRepository

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

class EIPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EipRepository(db)
        self.resource_bind_service = ResourceGroupService(self.db)

    # 创建eip
    def create_eip(self, user_id: int, data: EIPCreate):
        payload = {
            **data.model_dump(),
            "status": "AVAILABLE",
            "created_by": user_id,
            "internet_charge_type": "PayByTraffic",
            "public_ip": create_public_ip(data.region_id),
            "eip_id": f"vpc-{generate(size=12)}"
        }
        result = self.repo.create_eip(payload)
        if not result:
            return False

        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                user_id=user_id,
                resource_group_id=data.resource_group_id,
                resource_type="eip",
                resource_id=str(result),
            )
        )
        return result

    # eip分页列表
    def get_eip_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        eip_id: Optional[str] = None,
        public_ip: Optional[str] = None
    ):
        items, total = self.repo.eip_page_list(
            user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, eip_id, public_ip
        )
        item_out = [EIPOut.model_validate(s) for s in items]
        return EIPPage(
            total=total,
            page=page,
            page_size=page_size,
            items = item_out
        )


    # eip解绑，绑定，释放
    def eip_action(self, user_id: int, data: EIPSave):
        eip_find = self.repo.get_eip_by_id(data.eip_id)
        if eip_find is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if eip_find.status == 'ALLOCATING' or eip_find.status == 'BINDING':
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前eip状态不支持操作")

        if eip_find.created_by != user_id:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message="用户错误")

        result = self.repo.eip_action(data.status, data.eip_id)
        return result