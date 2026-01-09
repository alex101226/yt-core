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
from app.schemas.cmp.bill_schema import ProductOrderOut, ProductOrderPage, BillDetailPage, BillDetailOut

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

    # 商品订单
    def product_order_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        order: Optional[str] = None,
        instance_id: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None, ):
        items, total = self.order_repo.product_order_page_list(
            user_id, page, page_size, order, instance_id,
            start_at, end_at
        )
        out_items = [ProductOrderOut.model_validate(i) for i in items]
        return ProductOrderPage(total=total, page=page, page_size=page_size, items=out_items)

     # 订单明细
    def order_detail_page_list(
            self,
            user_id: int,
            page: int,
            page_size: int,
            instance_id: Optional[str] = None,
            consume_type: Optional[str] = None,
            provider_code: Optional[str] = None,
            billing_period: Optional[datetime] = None,
    ):
        items, total = self.detail_repo.bill_detail_page_list(
            user_id, page, page_size, instance_id, consume_type, provider_code,
            billing_period
        )
        return BillDetailPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[BillDetailOut.model_validate(item) for item in items],
        )

    # 扣费，创建资金流水
    def create_and_pay_order(
        self,
        *,
        user_id: int,
        account_id: int,
        instance_id: str,
        billing: BillingInstance,
        amount: Decimal,
        order_type: str,
        instance,
    ):
        now = datetime.now(timezone.utc)
        timestamp = datetime.now(timezone.utc).timestamp() * 1000

        meta = BILLING_META_MAP[ResourceType(billing.resource_type)]

        method_meta = BILLING_METHOD_META[BillingMethod(billing.billing_method)]

        cloud_provider_code = getattr(instance, "cloud_provider_code", None) or getattr(instance, "provider_code", None)
        order = Order(
            order_no=f"{billing.resource_type.value}-{timestamp}",
            bill_id= billing.id,
            instance_id=instance_id,
            cloud_provider_code=cloud_provider_code,
            product_id=0,
            business_id=0,
            product_name=meta.product_name,
            business_name=f"{meta.business_name}-{method_meta.text}",
            order_type=order_type,
            consume_type=method_meta.consume_type,
            amount_payable=amount,
            pay_status="PENDING",
            settlement_type="PLATFORM",
            charge_mode=billing.billing_method,
            auto_renew=billing.auto_renew,
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
            duration=billing.billing_period_count,
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

