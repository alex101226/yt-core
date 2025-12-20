from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

# 商品订单基础信息
class ProductOrderBase(BaseModel):
    order_no: str
    instance_id: str
    cloud_provider_code: str
    product_id: Optional[int] = 0
    product_name: str
    business_id:  Optional[int] = 0
    business_name: str
    order_type: str
    pay_status: str
    consume_type: str
    amount_payable: float
    use_credit: bool = False
    use_voucher: bool = False
    settlement_type: str
    account_id: int
    created_by: int

# 商品订单创建
class ProductOrderCreate(ProductOrderBase):
    pass

# 商品订单输出解析数据
class ProductOrderOut(ProductOrderBase):
    id: int
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 商品订单分页列表
class ProductOrderPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ProductOrderOut]

# 商品订单明细基础信息
class BillDetailBase(BaseModel):
    billing_period: Optional[str]
    region: Optional[str]
    billing_item_name: Optional[str]
    unit_price: float
    unit: Optional[str]
    duration: Optional[float] = 0
    coupon_amount: float = 0
    credit_amount: float = 0
    voucher_amount: float = 0
    balance_amount: float = 0
    owe_amount: float = 0

# 商品订单明细解析数据
class BillDetailOut(BillDetailBase):
    id: int
    created_at: Optional[datetime] = None

    order_no: Optional[str] = None
    instance_id: Optional[str] = None
    cloud_provider_code: Optional[str] = None
    product_id: Optional[int] = 0
    product_name: Optional[str] = None
    business_id: Optional[int] = 0
    business_name: Optional[str] = None
    consume_type: Optional[str] = None
    settlement_type: Optional[str] = None
    created_by: Optional[int] = None
    amount_payable: Optional[float] = None
    class Config:
        from_attributes = True

# 商品订单明细分页数据
class BillDetailPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BillDetailOut]