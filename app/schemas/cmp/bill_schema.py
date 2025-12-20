from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

class ProductOrderBase(BaseModel):
    order_no: str
    instance_id: str
    cloud_vendor: str
    product_name: str
    item_name: str
    order_type: str
    pay_status: str
    consume_type: str
    amount_payable: float
    use_balance: float = 0
    use_coupon: bool = False
    use_voucher: bool = False
    settlement_type: str
    account_id: int

class ProductOrderCreate(ProductOrderBase):
    pass


class ProductOrderOut(ProductOrderBase):
    id: int
    pay_status: Optional[str] = None
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProductOrderPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ProductOrderOut]