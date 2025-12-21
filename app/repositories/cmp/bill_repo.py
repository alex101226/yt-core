from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.funds_flow import FundsFlow
from app.models.cmp.product_order import ProductOrder
from app.models.cmp.product_order_detail import ProductOrderDetail

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
            ProductOrder.id, ProductOrder.order_no, ProductOrder.product_name, ProductOrder.product_id,
            ProductOrder.business_id, ProductOrder.business_name, ProductOrder.order_type,
            ProductOrder.pay_status, ProductOrder.consume_type, ProductOrder.amount_payable,
            ProductOrder.use_credit, ProductOrder.use_voucher, ProductOrder.settlement_type,
            ProductOrder.cloud_provider_code, ProductOrder.created_at, ProductOrder.paid_at,
            ProductOrder.instance_id, ProductOrder.account_id, ProductOrder.created_by
        )
        filters = [ProductOrder.created_by == user_id]

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
        return items, total

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
            ProductOrderDetail.id,
            ProductOrderDetail.order_id,
            ProductOrderDetail.billing_period,
            ProductOrderDetail.region,
            ProductOrderDetail.billing_item_name,
            ProductOrderDetail.unit_price,
            ProductOrderDetail.unit,
            ProductOrderDetail.duration,
            ProductOrderDetail.coupon_amount,
            ProductOrderDetail.credit_amount,
            ProductOrderDetail.voucher_amount,
            ProductOrderDetail.balance_amount,
            ProductOrderDetail.owe_amount,
            ProductOrderDetail.created_at,
            ProductOrder.order_no,
            ProductOrder.instance_id,
            ProductOrder.product_id,
            ProductOrder.product_name,
            ProductOrder.business_id,
            ProductOrder.business_name,
            ProductOrder.consume_type,
            ProductOrder.amount_payable,
            ProductOrder.settlement_type,
            ProductOrder.created_by,
            ProductOrder.account_id,
            ProductOrder.cloud_provider_code,
        ).outerjoin(ProductOrder, ProductOrder.id == ProductOrderDetail.order_id)

        filters = [ProductOrder.created_by == user_id]

        if instance_id:
            filters.append(ProductOrderDetail.instance_id.like(f'%{instance_id}%'))
        if provider_code:
            filters.append(ProductOrderDetail.cloud_vendor == provider_code)
        if consume_type:
            filters.append(ProductOrderDetail.consume_type == consume_type)
        if billing_period:
            # billing_period_str = billing_period.strftime("%Y-%m")
            filters.append(
                ProductOrderDetail.billing_period == billing_period
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(ProductOrderDetail.id.desc()).offset(offset_value).limit(page_size).all()
        # logger.info(f'查看这个信息 {items}')
        return items, total


    # 账单流水
    def get_billing_flows(
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
        offset = (page - 1) * page_size

        query = (
            self.db.query(
                ProductOrder.product_name,
                ProductOrder.business_name,
                ProductOrder.consume_type,  # 消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费
                ProductOrder.pay_status,
                ProductOrder.amount_payable,
                ProductOrder.settlement_type,
                ProductOrder.cloud_provider_code,
                ProductOrder.charge_mode,
                ProductOrderDetail.billing_period,
                ProductOrderDetail.coupon_amount,
                ProductOrderDetail.unit_price,
                ProductOrderDetail.balance_amount,
                ProductOrderDetail.credit_amount,
                ProductOrderDetail.voucher_amount,
                ProductOrderDetail.owe_amount,
                FundsFlow.id,
                FundsFlow.flow_no,
                FundsFlow.created_at.label("consume_time"),
                FundsFlow.ref_type,  # 订单类型：充值订单, 预付费场景,后付费 / 按量计费,退订/冲正
            )
            .join(ProductOrder, ProductOrder.id == ProductOrderDetail.order_id)
            .outerjoin(
                FundsFlow,
                (FundsFlow.ref_type == "BILLING_DETAIL") &
                (FundsFlow.ref_id == ProductOrderDetail.id)
            )
        )
        filters = [ProductOrder.created_by == user_id]
        # 可选查询条件
        if billing_id:
            filters.append(ProductOrderDetail.flow_no == billing_id)
        if start_month and end_month:
            # billing_period_str = billing_period.strftime("%Y-%m")
            filters.append(
                ProductOrderDetail.billing_period.between(start_month, end_month)
            )
        if consume_type:
            filters.append(ProductOrder.consume_type == consume_type)
        if billing_type:
            filters.append(FundsFlow.ref_type == billing_type)
        if cloud_provider_code:
            filters.append(ProductOrder.cloud_provider_code == cloud_provider_code)
        if billing_status:
            if billing_status == "已结算":
                filters.append(ProductOrder.pay_status == "SUCCESS")
            elif billing_status == "未结算":
                filters.append(ProductOrder.pay_status != "SUCCESS")

        if filters:
            query = query.filter(*filters)

        total = query.count()
        items = query.order_by(FundsFlow.id.desc()) \
            .offset(offset).limit(page_size) \
            .all()
        # 转换账单状态
        items_dict = [
            {
                "flow_no": row.flow_no,
                "consume_time": row.consume_time,
                "ref_type": row.ref_type,
                "charge_mode": row.charge_mode,
                "product_name": row.product_name,
                "business_name": row.business_name,
                "consume_type": row.consume_type,
                "pay_status": row.pay_status,
                "amount_payable": row.amount_payable,
                "settlement_type": row.settlement_type,
                "cloud_provider_code": row.cloud_provider_code,
                "billing_period": row.billing_period,
                "coupon_amount": row.coupon_amount,
                "unit_price": row.unit_price,
                "balance_amount": row.balance_amount,
                "credit_amount": row.credit_amount,
                "voucher_amount": row.voucher_amount,
                "owe_amount": row.owe_amount,
                "billing_status": "已结算" if row.pay_status == "SUCCESS" else "未结算"
            }
            for row in items
        ]
        logger.info(f'看下结果 {items_dict}')
        return items_dict, total

    # 收支明细
    def fund_detail_page_lis(
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
        query = self.db.query(FundsFlow)
        filters = [FundsFlow.user_id == user_id]

        if flow_no:
            filters.append(FundsFlow.flow_no.like(f'%{flow_no}%'))
        if third_trade_no:
            filters.append(FundsFlow.third_trade_no.like(f'%{third_trade_no}%'))

        if direction:
            filters.append(FundsFlow.direction==direction)
        if flow_type:
            filters.append(FundsFlow.flow_type==flow_type)
        if channel:
            filters.append(FundsFlow.channel==channel)

        # if fund_type:
        #     filters.append(FundsFlow.fund_type == fund_type)

        if start_at and end_at:
            filters.append(
                FundsFlow.created_at.between(start_at, end_at)
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(FundsFlow.id.desc()).offset(offset_value).limit(page_size).all()
        out_items = [
            {
                "id": row.id,
                "flow_no": row.flow_no,
                "direction": row.direction,
                "flow_type": row.flow_type,
                "fund_type": row.fund_type,
                "amount": row.amount,
                "balance_after": row.balance_after,
                "ref_type": row.ref_type,
                "ref_id": row.ref_id,
                "billing_period": row.billing_period,
                "channel": row.channel,
                "third_trade_no": row.third_trade_no,
                "description": row.description,
                "created_at": row.created_at,
            } for row in items
        ]
        return out_items, total

    # 月收支汇总
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
        query = self.db.query(
            FundsFlow.billing_period.label("month"),
            FundsFlow.direction,
            FundsFlow.flow_type,
            FundsFlow.channel,
            FundsFlow.fund_type,
            func.sum(FundsFlow.amount).label("total_amount"),
        ).filter(
            FundsFlow.user_id == user_id,
            FundsFlow.billing_period.between(start_month, end_month)
        )

        # 可选条件
        if direction:
            query = query.filter(FundsFlow.direction == direction)
        if flow_type:
            query = query.filter(FundsFlow.flow_type == flow_type)
        if channel:
            query = query.filter(FundsFlow.channel == channel)
        if flow_no:
            query = query.filter(FundsFlow.flow_no.like(f"%{flow_no}%"))
        # if third_trade_no:
        #     query = query.filter(FundsFlow.third_trade_no.like(f"%{third_trade_no}%"))

        # 分组
        query = query.group_by(
            FundsFlow.billing_period,
            FundsFlow.direction,
            FundsFlow.flow_type,
            FundsFlow.channel,
            FundsFlow.fund_type
        )

        # 分页
        total = query.count()  # 分组后的总条数
        offset_value = (page - 1) * page_size
        items = query.order_by("month").offset(offset_value).limit(page_size).all()

        out_items = [
            {
                "month": row.month,
                "direction": row.direction,
                "flow_type": row.flow_type,
                "channel": row.channel,
                "fund_type": row.fund_type,
                "total_amount": row.total_amount,
            }
            for row in items
        ]
        return out_items, total
