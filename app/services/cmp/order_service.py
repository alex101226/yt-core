from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from nanoid import generate

from app.constants.enums import ResourceType, BillingMethod

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.constants.billing_meta import BILLING_META_MAP, BILLING_METHOD_META
from app.schemas.cmp.bill_schema import ProductOrderOut, ProductOrderPage, BillDetailPage, BillDetailOut
from app.schemas.cmp.invoice_schema import InvoiceItemCreateSchema
from app.schemas.cmp.account_schema import FundsFlowCreate

from app.services.cmp.invoice_item_service import InvoiceItemService
from app.services.cmp.account_service import AccountService
from app.services.cmp.voucher_service import VoucherService
from app.models.cmp.billing_instance import BillingInstance

from app.repositories.cmp.order_repo import OrderRepo, OrderDetailRepo
from app.repositories.cmp.account_repo import AccountRepository
from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.cmp.credit_repo import CreditRepository

from app.models.cmp.order import Order
from app.models.cmp.order_detail import OrderDetail

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepo(db)
        self.detail_repo = OrderDetailRepo(db)
        self.account_service = AccountService(db)
        self.account_repo = AccountRepository(db)
        self.member_repo = MemberRepository(db)
        self.credit_repo = CreditRepository(db)
        self.voucher_service = VoucherService(db)
        self.invoice_item_service = InvoiceItemService(db)

    def _resolve_active_member_id(self, account_id: int) -> Optional[int]:
        account = self.account_repo.get_by_id(account_id)
        if not account:
            return None
        member = self.member_repo.get_active_by_user_id(account.created_by)
        return member.id if member else None

    def _consume_credit(
        self,
        member_id: int,
        cloud_provider_code: str,
        amount: Decimal,
        ref_type: str,
        ref_id: str,
        description: str,
        operator: dict,
    ) -> Decimal:
        if amount <= 0:
            return Decimal("0.00")

        now = datetime.utcnow()
        self.credit_repo.expire_grants(member_id, now)
        grants = self.credit_repo.active_grants_for_member(member_id, cloud_provider_code, now)
        remaining = amount
        consumed = Decimal("0.00")

        for grant in grants:
            if remaining <= 0:
                break
            grant_remaining = Decimal(str(grant.remaining_amount or 0)).quantize(
                Decimal("0.00"), rounding=ROUND_HALF_UP
            )
            if grant_remaining <= 0:
                continue
            use_amount = min(grant_remaining, remaining)
            grant.remaining_amount = (grant_remaining - use_amount).quantize(
                Decimal("0.00"), rounding=ROUND_HALF_UP
            )
            if grant.remaining_amount == 0:
                grant.status = "USED_UP"
            remaining = (remaining - use_amount).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
            consumed += use_amount
            self.credit_repo.create_flow({
                "grant_id": grant.id,
                "member_id": member_id,
                "amount": use_amount,
                "direction": "OUT",
                "flow_type": "CONSUME",
                "cloud_provider_code": cloud_provider_code,
                "ref_type": ref_type,
                "ref_id": ref_id,
                "description": description,
                "created_by": operator.get("user_id"),
                "created_by_name": operator.get("username"),
            })

        return consumed

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
        user: dict,
        account_id: int,
        instance_id: str,
        billing: BillingInstance,
        amount: Decimal,
        order_type: str,
        cloud_provider_code=str,
        region_id=str,
        use_credit: Optional[bool] = None,
        use_voucher: Optional[bool] = None,
    ):
        now = datetime.now(timezone.utc)
        timestamp = datetime.now(timezone.utc).timestamp() * 1000
        amount = Decimal(str(amount)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

        meta = BILLING_META_MAP[ResourceType(billing.resource_type)]

        method_meta = BILLING_METHOD_META[BillingMethod(billing.billing_method)]
        user_id = user.get('user_id')
        username = user.get('username')
        last_order = self.order_repo.get_last_product_order(instance_id)
        allow_voucher = use_voucher if use_voucher is not None else (
            bool(last_order.use_voucher) if order_type == "RENEW" and last_order else False
        )
        allow_credit = use_credit if use_credit is not None else (
            bool(last_order.use_credit) if order_type == "RENEW" and last_order else False
        )
        member_id = self._resolve_active_member_id(account_id)
        voucher_amount = Decimal("0.00")
        credit_amount = Decimal("0.00")
        balance_amount = amount

        if member_id and allow_voucher:
            voucher_amount = Decimal(
                str(self.voucher_service.consume(member_id, cloud_provider_code, float(amount)))
            ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
            if voucher_amount > amount:
                voucher_amount = amount
            balance_amount = (amount - voucher_amount).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

        # cloud_provider_code = getattr(instance, "cloud_provider_code", None) or getattr(instance, "provider_code", None)
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
            amount_payable=float(amount),
            pay_status="PENDING",
            use_credit=allow_credit,
            use_voucher=allow_voucher,
            settlement_type="PLATFORM",
            charge_mode=billing.billing_method,
            auto_renew=billing.auto_renew,
            account_id=account_id,
            created_at=now,
            created_by=user_id,
            created_by_name=username,
        )
        order_db = self.order_repo.create(order)

        if member_id and allow_credit and balance_amount > 0:
            credit_amount = self._consume_credit(
                member_id=member_id,
                cloud_provider_code=cloud_provider_code,
                amount=balance_amount,
                ref_type="PRODUCT_ORDER",
                ref_id=str(order_db.id),
                description=f"{meta.product_name}扣费抵用金抵扣",
                operator=user,
            ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
            if credit_amount > balance_amount:
                credit_amount = balance_amount
            balance_amount = (balance_amount - credit_amount).quantize(
                Decimal("0.00"), rounding=ROUND_HALF_UP
            )

        account = self.account_repo.get_by_id(account_id)
        if not account:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        current_balance = Decimal(str(account.balance or 0)).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )
        if balance_amount > 0 and current_balance <= Decimal("-5000.00"):
            raise BusinessException(code=ErrorCode.FAILED, message="账户欠费已达上限，请先充值")

        projected_balance = (current_balance - balance_amount).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )
        if balance_amount > 0 and projected_balance < Decimal("-5000.00"):
            raise BusinessException(code=ErrorCode.FAILED, message="账户欠费已达上限，请先充值")

        positive_balance = current_balance if current_balance > 0 else Decimal("0.00")
        paid_from_balance = min(positive_balance, balance_amount).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )
        owe_amount = (balance_amount - paid_from_balance).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )

        detail = OrderDetail(
            order_id=order.id,
            billing_period=now.strftime("%Y-%m"),
            billing_item_name=f"{meta.business_name}-{method_meta.text}",
            unit_price=billing.unit_price,
            unit=method_meta.unit,
            coupon_amount=float((voucher_amount + credit_amount).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)),
            credit_amount=float(credit_amount),
            voucher_amount=float(voucher_amount),
            balance_amount=float(paid_from_balance),
            owe_amount=float(owe_amount),
            created_at=now,
            duration=billing.billing_period_count,
            region=region_id
        )
        detail_db = self.detail_repo.create(detail)

        #   扣费，写入资金流水
        if balance_amount > 0:
            funds_flow_data = {
                "account_id": account_id,
                "flow_no": f"{datetime.now(timezone.utc).timestamp() * 1000}{order_db.id % 1000:03d}",
                "direction": "OUT",
                "flow_type": "PAY_ORDER",
                "fund_type": "BALANCE",
                "amount": balance_amount,
                "third_trade_no": order.order_no,
                "channel": "USER_ACCOUNT",
                "ref_type": "PRODUCT_ORDER",
                "ref_id": order_db.id,
                "billing_period": datetime.now().strftime("%Y-%m"),
                "description": f"{meta.product_name}扣费",
                "created_by": user_id,
                "created_by_name": username,
            }

            fund_pay = self.account_service.pay(funds_flow_data)
            if not fund_pay:
                raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)

        order.pay_status = "SUCCESS"
        order.paid_at = now

        # 写发票
        invoice_product_name = f"{method_meta.text}-{detail_db.billing_period}-{order_db.product_name}"

        invoice = InvoiceItemCreateSchema(
            created_by=user_id,
            created_by_name=username,
            billing_period=detail_db.billing_period,
            billing_period_start= billing.last_billing_time or billing.billing_start_time,
            billing_period_end=billing.billing_end_time,
            cloud_provider_code=billing.cloud_provider_code,
            cloud_provider_name="阿里云",
            order_type=order_db.order_type,
            product_display_name=invoice_product_name,
            origin_order_no=order_db.order_no,
            instance_id=order_db.instance_id,
            paid_amount=float(amount),
            invoice_amount=float(amount),
            paid_at=order_db.paid_at
        )
        self.invoice_item_service.create_invoice_item(invoice)
