from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.constants.enums import InvoiceItemStatus, InvoiceRecordStatus

from app.repositories.cmp.invoice_item_repo import InvoiceItemRepo

from app.schemas.cmp.invoice_schema import InvoiceItemCreateSchema, InvoiceRecordSchema


class InvoiceItemService:
    def __init__(self, db: Session):
        self.db = db
        self.invoice_item_repo = InvoiceItemRepo(db)

    # 创建
    def create_invoice_item(self, invoice_item: InvoiceItemCreateSchema):
        payload = {
            **invoice_item.model_dump(),
            "currency": "CNY",
            "status": "UNISSUED",
            "target_type": "BILL"
        }

        result = self.invoice_item_repo.create_invoice_item(payload)
        return result


    # 列表数据
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
        items, total = self.invoice_item_repo.page_list(
            user_id, page, page_size, paid_start, paid_end,
            amount_min, amount_max, billing_period
        )
        return {
            "items": items,
            "total": total,
            "page_size": page_size,
            "page": page,
        }

        # 欠票记录

    def page_list_overdue(
            self,
            user_id: int,
            page: int,
            page_size: int,
    ):
        items, total = self.invoice_item_repo.page_list_overdue(
            user_id,
            page,
            page_size,
        )
        return {
            "items": items,
            "total": total,
            "page_size": page_size,
            "page": page,
        }


    # 开票记录创建
    def create_invoice_record(self, user_id: int, data: InvoiceRecordSchema):
        payload = {
            **data.model_dump(),
            "status": InvoiceRecordStatus.ISSUED.value,
            "user_id": user_id,
            "issued_at": datetime.now(timezone.utc),
            "invoice_no":datetime.now(timezone.utc).timestamp() * 1000
        }
        invoice_record = self.invoice_item_repo.create_invoice_record(payload)
        return invoice_record


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
        items, total = self.invoice_item_repo.page_list_record_issued(
            user_id, page, page_size, status, apply_start, apply_end, invoice_no
        )
        return {
            "items": items,
            "total": total,
            "page_size": page_size,
            "page": page,
        }

    def get_invoice_statistics(self, user_id: int):
        return self.invoice_item_repo.get_invoice_statistics(user_id)