from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.constants.enums import InvoiceItemStatus
from app.core.logger import logger
from app.models.cmp.invoice_item import InvoiceItem

from app.models.cmp.invoice_record import InvoiceRecord

class InvoiceItemRepo:
    def __init__(self, db: Session):
        self.db = db

    # 创建发票记录
    def create_invoice_item(self, invoice_item: dict):
        invoice_item = InvoiceItem(**invoice_item)
        self.db.add(invoice_item)
        self.db.flush()
        return invoice_item


    # page_list
    def page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        paid_start: Optional[datetime] = None,
        paid_end: Optional[datetime] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        billing_period: Optional[str] = None,
    ):
        query = self.db.query(InvoiceItem).order_by(InvoiceItem.id.desc())

        filters = [
            InvoiceItem.created_by == user_id,
            InvoiceItem.is_released == 0,
            InvoiceItem.status==InvoiceItemStatus.UNISSUED.value
        ]

        # 支付时间区间
        if paid_start and paid_end:
            filters.append(InvoiceItem.paid_at.between(paid_start, paid_end))
        elif paid_start:
            filters.append(InvoiceItem.paid_at >= paid_start)
        elif paid_end:
            filters.append(InvoiceItem.paid_at <= paid_end)

        # 实付金额范围
        if amount_min is not None and amount_max is not None:
            filters.append(InvoiceItem.paid_amount.between(amount_min, amount_max))
        elif amount_min is not None:
            filters.append(InvoiceItem.paid_amount >= amount_min)
        elif amount_max is not None:
            filters.append(InvoiceItem.paid_amount <= amount_max)

        # 账期
        if billing_period:
            filters.append(InvoiceItem.billing_period.like(f"%{billing_period}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.offset(offset_value).limit(page_size).all()
        return items, total

    # 开具发票操作
    def create_invoice_record(self, data: dict):
        """
        创建一条发票记录，并更新对应可开票记录状态
        """
        invoice_item_ids = data['invoice_item_ids']
        if not invoice_item_ids:
            return None

        # 查询所有选中的可开票记录
        invoice_items = self.db.query(InvoiceItem) \
            .filter(InvoiceItem.id.in_(invoice_item_ids)) \
            .with_for_update() \
            .all()

        if not invoice_items:
            return None

        # 计算总金额
        total_amount = Decimal("0")
        for item in invoice_items:
            if item.status != InvoiceItemStatus.UNISSUED:
                return None
            total_amount += Decimal(str(item.invoice_amount))

        invoice_record = InvoiceRecord(**data)
        self.db.add(invoice_record)

        # 更新 InvoiceItem 状态为已开票
        for item in invoice_items:
            issued = Decimal(str(item.invoice_amount))
            # 累加已开票金额
            item.issued_amount = (
                Decimal(str(item.issued_amount or 0)) + issued
            )
            # 剩余可开票金额清零
            item.invoice_amount = 0

            # item.invoice_amount = 0  # 已开票金额清零
            item.status = InvoiceItemStatus.ISSUED
            item.updated_at = datetime.now(timezone.utc)
            item.issued_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(invoice_record)
        return invoice_record

    # 欠票记录
    def page_list_overdue(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ):
        overdue_time = datetime.now(timezone.utc) - timedelta(days=180)

        query = self.db.query(InvoiceItem).order_by(InvoiceItem.paid_at.asc())

        filters = [
            InvoiceItem.created_by == user_id,
            InvoiceItem.is_released == 0,
            InvoiceItem.status == InvoiceItemStatus.UNISSUED.value,
            InvoiceItem.invoice_amount > 0,
            InvoiceItem.paid_at <= overdue_time,
        ]

        query = query.filter(*filters)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    # 开票记录
    def page_list_record_issued(
        self,
        user_id: int,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        apply_start: Optional[datetime] = None,
        apply_end: Optional[datetime] = None,
        invoice_no: Optional[str] = None,
    ):
        query = self.db.query(InvoiceRecord).order_by(InvoiceRecord.id.desc())

        filters = [InvoiceRecord.created_by == user_id]

        # 发票状态
        if status:
            filters.append(InvoiceRecord.status == status)

        # 发票号
        if invoice_no:
            filters.append(InvoiceRecord.invoice_no.like(f"%{invoice_no}%"))

        # 申请时间区间
        if apply_start and apply_end:
            filters.append(InvoiceRecord.created_at.between(apply_start, apply_end))
        elif apply_start:
            filters.append(InvoiceRecord.created_at >= apply_start)
        elif apply_end:
            filters.append(InvoiceRecord.created_at <= apply_end)

        query = query.filter(*filters)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total

    # 统计
    def get_invoice_statistics(self, user_id: int):
        now = datetime.now(timezone.utc)

        # 本月起始
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1️⃣ 可开票金额
        available_amount = self.db.query(
            func.coalesce(func.sum(InvoiceItem.invoice_amount), 0)
        ).filter(
            InvoiceItem.created_by == user_id,
            InvoiceItem.status == InvoiceItemStatus.UNISSUED.value,
            InvoiceItem.invoice_amount > 0,
            InvoiceItem.is_released == 0,
        ).scalar()

        # 2️⃣ 总计消费可开票金额
        total_consumed_amount = self.db.query(
            func.coalesce(func.sum(InvoiceItem.paid_amount), 0)
        ).filter(
            InvoiceItem.created_by == user_id,
            InvoiceItem.is_released == 0,
        ).scalar()

        # 3️⃣ 历史已开票金额
        total_issued_amount = self.db.query(
            func.coalesce(func.sum(InvoiceItem.issued_amount), 0)
        ).filter(
            InvoiceItem.created_by == user_id,
            InvoiceItem.status == InvoiceItemStatus.ISSUED.value,
        ).scalar()

        # 4️⃣ 本月不可开票金额（示例：T+1）
        unavailable_amount = self.db.query(
            func.coalesce(func.sum(InvoiceItem.invoice_amount), 0)
        ).filter(
            InvoiceItem.created_by == user_id,
            InvoiceItem.status == InvoiceItemStatus.UNISSUED.value,
            InvoiceItem.paid_at >= month_start,
            InvoiceItem.paid_at > now - timedelta(days=1),
            InvoiceItem.is_released == 0,
        ).scalar()

        return {
            "available_invoice_amount": Decimal(available_amount),
            "total_consumed_invoice_amount": Decimal(total_consumed_amount),
            "total_issued_invoice_amount": Decimal(total_issued_amount),
            "current_month_unavailable_amount": Decimal(unavailable_amount),
        }