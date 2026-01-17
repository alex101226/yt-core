from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.services.cmp.order_service import OrderService

from app.models.cmp.billing_instance import BillingMethod, BillingInstance, ResourceType, BillingCycle, BillingStatus

from app.repositories.cmp.bill_repo import BillRepository
from app.schemas.cmp.bill_schema import ProductOrderOut, ProductOrderPage, BillDetailOut, BillDetailPage

# 计算下次的时间
def calc_next_billing_time(
    *,
    now: datetime,
    billing_cycle: str,
    period_count: int
) -> datetime:
    if billing_cycle == "HOUR":
        next_billing_due = now + timedelta(weeks=1)
        # return now + timedelta(hours=period_count)
        return next_billing_due

    if billing_cycle == "MONTH":
        return now + relativedelta(months=period_count)

    raise ValueError(f"Unsupported billing_cycle: {billing_cycle}")

class BillService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BillRepository(db)
        self.order_service = OrderService(db)

    # 账单流水
    def billing_flows_page_list(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        billing_id: int = None,
        start_month: str = None,  # "YYYY-MM"
        end_month: str = None,  # "YYYY-MM"
        consume_type: str = None,
        billing_type: str = None,
        cloud_provider_code: str = None,
        billing_status: str = None,  # '已结算' / '未结算'
    ):
        items, total = self.repo.get_billing_flows(
            user_id, page, page_size, billing_id, start_month, end_month,
            consume_type, billing_type, cloud_provider_code, billing_status
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }



    # 收支明细
    def billing_flow_detail_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        flow_no: Optional[str] = None,
        third_trade_no: Optional[str] = None,
        direction: Optional[str] = None,
        flow_type: Optional[str] = None,
        channel: Optional[str] = None,
        # fund_type: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
    ):
        items, total = self.repo.fund_detail_page_lis(
            user_id, page, page_size, flow_no, third_trade_no, direction, flow_type,
            channel, start_at, end_at
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }


    # 月汇总
    def monthly_fund_summary(
        self,
        user_id: int,
        page: int,
        page_size: int,
        start_month: str,  # "YYYY-MM"
        end_month: str,  # "YYYY-MM"
        direction: Optional[str] = None,
        flow_type: Optional[str] = None,
        channel: Optional[str] = None,
        flow_no: Optional[str] = None,
        # third_trade_no: Optional[str] = None,
    ):
        items, total = self.repo.monthly_fund_summary(
            user_id, page, page_size, start_month, end_month, direction, flow_type,
            channel, flow_no
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }


    # 创建计费任务
    def create(
        self, *,
        user_id: int,
        account_id: int,
        resource_type: str,
        charge_type: str,
        instance_id: str,
        instance,
        unit_price: float):
        now = datetime.now(timezone.utc)
        period_months = getattr(instance, "period", 1)
        # 单价金额
        amount = Decimal(str(unit_price))
        # 计费方式
        # charge_type = instance.instance_charge_type  # PrePaid / PostPaid

        # 计费单位
        billing_cycle = "HOUR" if charge_type == "PostPaid" else "MONTH"

        # 云厂商
        cloud_provider_code = getattr(instance, "cloud_provider_code", None) or getattr(instance, "provider_code", None)

        # 结束计费时间
        if charge_type == "PrePaid":
            billing_end_time = now + relativedelta(months=+period_months)
        else:
            billing_end_time = None  # PostPaid 不需要

        # 1️⃣ 创建计费实例
        billing_instance = BillingInstance(
            resource_type=resource_type,    # 收费服务type
            resource_id=instance.id, # 实例服务的id
            billing_method=charge_type,
            billing_cycle=billing_cycle,    # 计费周期：HOUR / MONTH。要根据计费单位修改单位，先记下来
            unit_price=amount,  # 单价（元/小时 或 元/月）
            billing_start_time=now, # 开始计费时间
            billing_end_time= billing_end_time,   # 结束扣费时间
            last_billing_time=None, # 上一次成功结算到的时间
            auto_renew=getattr(instance, 'auto_renew', False) if instance else False,
            status=BillingStatus.CREATED,    #   已创建
            billing_period_count = period_months,
            cloud_provider_code=cloud_provider_code,
            region_id=getattr(instance, 'region_id'),
        )
        # 创建计费任务
        billing_db = self.repo.bill_create(billing_instance)

        self._first_charge(user_id, account_id, instance_id, billing_db)

        return billing_db


    # 创建订单，扣费任务，资金流水
    def _first_charge(self, user_id: int, account_id: int, instance_id: str, billing: BillingInstance):
        now = datetime.now(timezone.utc)
        # 1 小时
        amount = billing.unit_price * billing.billing_period_count

        # 创建订单
        self.order_service.create_and_pay_order(
            user_id=user_id,
            account_id=account_id,
            instance_id=instance_id,
            billing=billing,
            amount=amount,
            order_type="CREATE",
            cloud_provider_code=billing.cloud_provider_code,
            region_id=billing.region_id,
        )
        next_time = calc_next_billing_time(
            now=now,
            billing_cycle=billing.billing_cycle.value,
            period_count=billing.billing_period_count
        )

        # 更新计费时间
        self.repo.bill_update(
            billing_id = billing.id,
            last_time=now,
            next_time=next_time,
            status=BillingStatus.ACTIVE,
        )