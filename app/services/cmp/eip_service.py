from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.core.logger import logger
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException
from app.common.ipaddress import create_public_ip

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPOut, EIPPage, EIPSave
from app.repositories.cmp.eip_repo import EipRepository

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.account_service import AccountService
from app.schemas.cmp.account_schema import FundsFlowCreate

class EIPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EipRepository(db)
        self.resource_bind_service = ResourceGroupService(self.db)
        self.account_service = AccountService(self.db)

    # 创建eip
    def create_eip(self, user_id: int, data: EIPCreate):
        try:
            with self.db.begin():
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
                    raise BusinessException(code=ErrorCode.FAILED, message="eip创建失败")

                # ⚠️ 按量计费：这里只校验账户是否存在
                account = self.account_service.account_recharge_exists(user_id)
                if not account:
                    raise BusinessException(code=ErrorCode.FAILED, message="请先开通账户")

                resource_data = ResourceGroupBindingCreate(
                    cloud_provider_code=data.cloud_provider_code,
                    user_id=user_id,
                    resource_group_id=data.resource_group_id,
                    resource_type="eip",
                    resource_id=str(result.id),
                )
                self.resource_bind_service.bind(resource_data)

                time = datetime.now(timezone.utc)
                self.settle_eip_hourly(account, user_id, result, time, time)
            return result
        except BusinessException as exception:
            self.db.rollback()
            raise exception

    # EIP 按量结算
    def settle_eip_hourly(self, account, user_id: int, eip, start_at, end_at):
        last_order = self.account_service.get_last_product_order(eip.eip_id)
        if not last_order:
            order_type = "CREATE"
        elif last_order.amount_payable != eip.price:
            order_type = "UPGRADE"
        else:
            order_type = "RENEW"

        # 1. 创建商品订单 支付状态：PENDING/SUCCESS/FAILED
        order = self.account_service.product_create({
            "order_no": f"EIP-{generate(size=10)}",
            "instance_id": eip.eip_id,
            "cloud_provider_code": eip.cloud_provider_code,
            "product_id": 0,
            "product_name": "弹性公网EIP",
            "business_id": 0,
            "business_name": f'{eip.eip_name}按量付费',
            "order_type": order_type,
            "pay_status": "PENDING",
            "consume_type": "VOLUME_BASED",
            "amount_payable": eip.price,
            "use_credit": False,
            "use_voucher": False,
            "settlement_type": "PLATFORM",
            "account_id": account.id,
            "created_by": eip.created_by,
            "charge_mode": "POSTPAID",
        })

        # 创建订单明细
        bill_order = self.account_service.bill_details_create({
            "billing_period": start_at.strftime("%Y-%m"),
            "region": eip.region_id,
            "billing_item_name": "EIP公网宽带",
            "unit_price": eip.price,
            "unit": "HOUR",
            "duration": 1,
            "coupon_amount": 0,
            "credit_amount": 0,
            "balance_amount": eip.price,
            "voucher_amount": 0,
            "owe_amount": 0,
            "order_id": order.id
        })

        try:
            # 2. 扣费
            funds_flow_data = {
                "user_id": user_id,
                "account_id": account.id,
                "flow_no": f"{datetime.now(timezone.utc).timestamp() * 1000}{order.id % 1000:03d}",
                "direction": "OUT",
                "flow_type": "PAY_ORDER",
                "fund_type": "BALANCE",
                "amount": eip.price,
                "ref_type": "BILLING_DETAIL",
                "ref_id": order.id,
                "billing_period": datetime.now().strftime("%Y-%m"),
                "channel": "USER_ACCOUNT",
                "third_trade_no": order.order_no,
                "description": f"{bill_order.billing_item_name}扣费",
                "created_by": user_id,
            }
            self.account_service.pay(account.balance, funds_flow_data)
            order.pay_status = "SUCCESS"
            order.paid_at = datetime.now(timezone.utc)
        except BusinessException:
            logger.info(f'这里是扣款失败了')
            order.pay_status = "FAILED"
            bill_order.owe_amount = eip.price

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

        if eip_find.created_by != user_id:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message="用户错误")

        result = self.repo.eip_action(data.status, data.eip_id)
        return result

    # 绑定eip
    def allocate_eip(self, provider_code: str, region_id: str, instance_id: int, internet_charge_type: str):
        eip = self.repo.get_free_eip(provider_code, region_id, internet_charge_type)

        if not eip:
            return None
            # raise BusinessException(
            #     code=ErrorCode.RESOURCE_BINDING_FAILED,
            #     message="暂无可用的eip"
            # )

        # 绑定
        eip.status = "BOUND"
        eip.bind_instance_id = str(instance_id)

        return eip.public_ip