from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.repositories.cmp.bill_repo import BillRepository
from app.schemas.cmp.bill_schema import ProductOrderOut, ProductOrderPage, BillDetailOut, BillDetailPage

class BillService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BillRepository(db)

    # 商品订单
    def product_order_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        order: Optional[str] = None,
        instance_id: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,):
        items, total = self.repo.product_order_page_list(user_id, page, page_size, order, instance_id, start_at, end_at)
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
        items, total = self.repo.bill_detail_page_list(
            user_id, page, page_size, instance_id, consume_type, provider_code,
            billing_period
        )
        return BillDetailPage(
            total=total,
            page=page,
            page_size=page_size,
            items = [BillDetailOut.model_validate(item) for item in items],
        )

    # 账单流水
    def billing_flows_page_list(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        billing_id: int = None,
        billing_period: str = None,
        consume_type: str = None,
        billing_type: str = None,
        cloud_provider_code: str = None,
        billing_status: str = None,  # '已结算' / '未结算'
    ):
        items, total = self.repo.get_billing_flows(
            user_id, page, page_size, billing_id, billing_period,
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
        fund_type: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
    ):
        items, total = self.repo.fund_detail_page_lis(
            user_id, page, page_size, flow_no, third_trade_no, direction, flow_type,
            channel, fund_type, start_at, end_at
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
        third_trade_no: Optional[str] = None,
    ):
        items, total = self.repo.monthly_fund_summary(
            user_id, page, page_size, start_month, end_month, direction, flow_type,
            channel, flow_no, third_trade_no
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }