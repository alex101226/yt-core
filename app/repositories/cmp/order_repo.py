from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.order import Order
from app.models.cmp.order_detail import OrderDetail

class OrderRepo:
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
            Order.id, Order.order_no, Order.product_name, Order.product_id,
            Order.business_id, Order.business_name, Order.order_type,
            Order.pay_status, Order.consume_type, Order.amount_payable,
            Order.use_credit, Order.use_voucher, Order.settlement_type,
            Order.cloud_provider_code, Order.created_at, Order.paid_at,
            Order.instance_id, Order.account_id, Order.created_by
        )
        filters = [Order.created_by == user_id]

        if order:
            filters.append(Order.order_no.like(f'%{order}%'))
        if instance_id:
            filters.append(Order.instance_id.like(f'%{instance_id}%'))

        if start_at and end_at:
            filters.append(
                Order.created_at.between(start_at, end_at)
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(Order.id.desc()).offset(offset_value).limit(page_size).all()
        logger.info(f'查看这张表数据 {items}')
        return items, total


    # 创建订单
    def create(self, data: Order):
        # order_db = Order(**data)
        self.db.add(data)
        self.db.flush()
        return data

    # 查找订单
    def get_last_product_order(self, instance_id: str):
        return self.db.query(Order).filter(Order.instance_id == instance_id).first()


class OrderDetailRepo:
    def __init__(self, db: Session):
        self.db = db

    # 账单明细  消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费
    def bill_detail_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        instance_id: Optional[str] = None,
        consume_type: Optional[str] = None,
        provider_code: Optional[str] = None,
        billing_period: Optional[str] = None,
    ):
        query = self.db.query(
            OrderDetail.id,
            OrderDetail.order_id,
            OrderDetail.billing_period,
            OrderDetail.region,
            OrderDetail.billing_item_name,
            OrderDetail.unit_price,
            OrderDetail.unit,
            OrderDetail.duration,
            OrderDetail.coupon_amount,
            OrderDetail.credit_amount,
            OrderDetail.voucher_amount,
            OrderDetail.balance_amount,
            OrderDetail.owe_amount,
            OrderDetail.created_at,
            Order.order_no,
            Order.instance_id,
            Order.product_id,
            Order.product_name,
            Order.business_id,
            Order.business_name,
            Order.consume_type,
            Order.amount_payable,
            Order.settlement_type,
            Order.created_by,
            Order.account_id,
            Order.cloud_provider_code,
        ).outerjoin(Order, Order.id == OrderDetail.order_id)

        filters = [Order.created_by == user_id]

        if instance_id:
            filters.append(OrderDetail.instance_id.like(f'%{instance_id}%'))
        if provider_code:
            filters.append(OrderDetail.cloud_vendor == provider_code)
        if consume_type:
            filters.append(OrderDetail.consume_type == consume_type)
        if billing_period:
            # billing_period_str = billing_period.strftime("%Y-%m")
            filters.append(
                OrderDetail.billing_period == billing_period
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(OrderDetail.id.desc()).offset(offset_value).limit(page_size).all()
        # logger.info(f'查看这个信息 {items}')
        return items, total


    # 创建明细
    def create(self, data: OrderDetail):
        # detail_db = OrderDetail(**data)
        self.db.add(data)
        self.db.flush()
        return data