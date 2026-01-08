from os import times

from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from nanoid import generate

from app.constants.enums import ResourceType, BillingMethod

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.constants.billing_meta import BILLING_META_MAP, BILLING_METHOD_META

from app.services.cmp.account_service import AccountService
from app.repositories.cmp.bill_repo import BillRepository
from app.models.cmp import BillingInstance

from app.repositories.cmp.order_repo import OrderRepo, OrderDetailRepo

from app.models.cmp.order import Order
from app.models.cmp.order_detail import OrderDetail

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepo(db)
        self.detail_repo = OrderDetailRepo(db)
        self.bill_repo = BillRepository(db)
        self.account_service = AccountService(db)

    # 生成订单
    def create_order(self, *, data: dict):

        timestamp = datetime.now(timezone.utc).timestamp() * 1000

        product_payload = {
            **data,
            "pay_status": "PENDING",
            "order_no": f"ORDER-{timestamp}",
            "instance_id": data['instance_id'],
            "cloud_provider_code": data['cloud_provider_code'],
            "product_id": data['product_id'],
            "product_name": data['product_name'],
            "business_id": data['business_id'],
            "business_name": data['business_name'],
            "order_type": data['order_type'],
            "consume_type": data['consume_type'],  # 消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费
            "amount_payable": data['amount_payable'],
            "use_credit": data['use_credit'],
            "use_voucher": data['use_voucher'],
            "settlement_type": data['settlement_type'],
            "account_id": data['account_id'],
            "created_by": data['created_by'],
            "charge_mode": data['charge_mode'],
        }

        # 创建订单
        product_result = self.order_repo.create(product_payload)
        if not product_result:
            raise BusinessException(code=ErrorCode.FAILED, message="订单创建失败")

        bill_payload = {
            "billing_period": data['billing_period'],
            "region": data['region'],
            "billing_item_name": data['billing_item_name'],
            "unit_price": data['price'],
            "unit": "HOUR",
            "duration": data['duration'],
            "coupon_amount": data['coupon_amount'],
            "credit_amount": data['credit_amount'],
            "balance_amount": data['price'],
            "voucher_amount": data['voucher_amount'],
            "owe_amount": data['owe_amount'],
            "order_id": product_result.id
        }
        # 创建订单明细
        bill_result = self.create_order_detail(bill_payload)
        return {
            **product_result,
            **bill_result,
        }

    # 创建订单明细
    def create_order_detail(self, data: dict):
        billing_detail = self.detail_repo.create(data)
        if not billing_detail:
            raise BusinessException(code=ErrorCode.FAILED, message="账单明细创建失败")
        return billing_detail

    # 扣费，创建资金流水
    def create_and_pay_order(
        self,
        *,
        user_id: int,
        account_id: int,
        billing: BillingInstance,
        amount: Decimal,
        order_type: str,
        instance,
    ):
        now = datetime.now(timezone.utc)
        timestamp = datetime.now(timezone.utc).timestamp() * 1000

        meta = BILLING_META_MAP[ResourceType(billing.resource_type)]

        method_meta = BILLING_METHOD_META[BillingMethod(billing.billing_method)]

        order = Order(
            order_no=f"{billing.resource_type.value}-{timestamp}",
            instance_id=billing.resource_id,
            product_id=0,
            business_id=0,
            cloud_provider_code=instance.cloud_provider_code,
            product_name=meta.product_name,
            business_name=f"{meta.business_name}-{method_meta.text}",
            order_type=order_type,
            consume_type=method_meta.consume_type,
            amount_payable=amount,
            pay_status="PENDING",
            settlement_type="PLATFORM",
            charge_mode=billing.billing_method,
            auto_renew=instance.auto_renew,
            account_id=account_id,
            created_at=now,
            created_by=user_id,
        )
        order_db = self.order_repo.create(order)

        detail = OrderDetail(
            order_id=order.id,
            billing_period=now.strftime("%Y-%m"),
            billing_item_name=f"{meta.business_name}-{method_meta.text}",
            unit_price=billing.unit_price,
            unit=method_meta.unit,
            balance_amount=amount,
            owe_amount=0,
            created_at=now,
            duration=instance.period,
            region=instance.region_id
        )
        self.detail_repo.create(detail)

        #   扣费，写入资金流水
        funds_flow_data = {
            "user_id": user_id,
            "account_id": account_id,
            "flow_no": f"{datetime.now(timezone.utc).timestamp() * 1000}{order_db.id % 1000:03d}",
            "third_trade_no": order.order_no,
            "channel": "USER_ACCOUNT",
            "direction": "OUT",
            "flow_type": "PAY_ORDER",
            "fund_type": "BALANCE",
            "ref_type": "PRODUCT_ORDER",
            "ref_id": order_db.id,
            "billing_period": datetime.now().strftime("%Y-%m"),
            "amount": amount,
            "description": f"{meta.product_name}扣费",
            "created_by": user_id
        }
        self.account_service.pay(funds_flow_data)

        order.pay_status = "SUCCESS"
        order.paid_at = now

        # self.db.commit()

