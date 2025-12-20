from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.testing.pickleable import Order

from app.core.logger import logger

from app.models.cmp.recharge_order import RechargeOrder
from app.models.cmp.billing_flow import BillingFlow
from app.models.cmp.product_order import ProductOrder
from app.models.cmp.billing_detail import BillingDetail

class BillRepository:
    def __init__(self, db: Session):
        self.db = db

    # 商品订单
    def product_order_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        order: Optional[str] = None,
        instance_id: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
    ):
        query = self.db.query(
            ProductOrder.id, ProductOrder.order_no, ProductOrder.product_name,
            ProductOrder.item_name, ProductOrder.order_type, ProductOrder.pay_status,
            ProductOrder.consume_type, ProductOrder.amount_payable, ProductOrder.use_balance,
            ProductOrder.use_coupon, ProductOrder.use_voucher, ProductOrder.settlement_type,
            ProductOrder.cloud_vendor, ProductOrder.created_at, ProductOrder.paid_at,
            ProductOrder.instance_id, ProductOrder.account_id,
        )
        filters = [ProductOrder.account_id == user_id]

        if order:
            filters.append(ProductOrder.order_no.like(f'%{order}%'))
        if instance_id:
            filters.append(ProductOrder.instance_id.like(f'%{instance_id}%'))

        if start_at and end_at:
            filters.append(
                ProductOrder.created_at.between(start_at, end_at)
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(ProductOrder.id.desc()).offset(offset_value).limit(page_size).all()
        logger.info(f'查看数据 {items}')
        return items, total


