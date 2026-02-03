from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.core.logger import logger
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException
from app.common.ipaddress import create_public_ip

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService
from app.schemas.cmp.account_schema import FundsFlowCreate

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPOut, EIPPage, EIPSave
from app.repositories.cmp.eip_repo import EipRepository
from app.services.cmp.operation_helper import execute_with_notification

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

class EIPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EipRepository(db)
        self.resource_bind_service = ResourceGroupService(self.db)
        self.account_service = AccountService(self.db)
        self.bill_service = BillService(db)

    # 生成计费任务
    def create_initial_bill(
        self,
        user: dict,
        charge_type: str,
        instance_id: str,
        unit_price: float,
        instance,
    ):
        account = self.account_service.account_exists(user.get('user_id'))
        if not account:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="EIP",
            charge_type=charge_type,
            instance_id=instance_id,
            instance=instance,
            unit_price=unit_price,
        )

    # 创建eip
    def create_eip(self, user: dict, data: EIPCreate):
        user_id = user.get('user_id')
        username = user.get('username')
        def _do():
            try:
                with self.db.begin():
                    payload = {
                        **data.model_dump(),
                        "status": "AVAILABLE",
                        "created_by": user_id,
                        "created_by_name": username,
                        "internet_charge_type": "PayByTraffic",
                        "public_ip": create_public_ip(data.region_id),
                        "eip_id": f"vpc-{generate(size=12)}"
                    }
                    payload.pop('price')
                    result = self.repo.create_eip(payload)
                    if not result:
                        raise BusinessException(code=ErrorCode.FAILED, message="eip创建失败")

                    account = self.account_service.account_recharge_exists(user_id)
                    if not account:
                        raise BusinessException(code=ErrorCode.FAILED, message="请先开通账户")

                    self.create_initial_bill(
                        user, "PostPaid", result.eip_id, data.price, result,
                    )
                    resource_data = ResourceGroupBindingCreate(
                        cloud_provider_code=data.cloud_provider_code,
                        created_by=user_id,
                        created_by_name=username,
                        resource_group_id=data.resource_group_id,
                        resource_type="eip",
                        resource_id=str(result.id),
                    )
                    self.resource_bind_service.bind(resource_data)
                return result
            except BusinessException as exception:
                self.db.rollback()
                raise exception

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="EIP",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="弹性公网（EIP）创建成功",
            failed_desc="弹性公网（EIP）创建失败",
            func=_do
        )

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

    # 查询所有的eip
    def list_all_volume_based_eip(self):
        return self.repo.list_all_volume_based_eip()

    # eip解绑，绑定，释放
    def eip_action(self, user_id: int, data: EIPSave):
        eip_find = self.repo.get_eip_by_id(data.eip_id)

        if eip_find is None:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if eip_find.status == 'ALLOCATING' or eip_find.status == 'BINDING':
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前eip状态不支持操作")

        result = self.repo.eip_action(data.status, data.eip_id)
        return result

    # 绑定eip
    def allocate_eip(self, provider_code: str, region_id: str, instance_id: int):
        eip = self.repo.get_free_eip(provider_code, region_id)

        if not eip:
            return None
        # 绑定
        eip.status = "BOUND"
        eip.bind_instance_id = str(instance_id)

        return eip.public_ip


