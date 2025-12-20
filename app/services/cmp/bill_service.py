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
from app.schemas.cmp.bill_schema import ProductOrderOut, ProductOrderPage

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