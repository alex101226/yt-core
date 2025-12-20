from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List

class AccountRecharge(BaseModel):
    balance: float

class AccountCreate(BaseModel):
    pay_channel: str
    amount: Decimal

class ProductOrderCreate(BaseModel):
    order_no: str
    instance_id: str
    cloud_vendor: str
    product_name: str
    item_name: str
    order_type: str
    pay_status: str
    consume_type: str
    amount_payable: float
    use_balance: bool = True
    use_coupon: bool = False
    use_voucher: bool = False
    settlement_type: str
    account_id: int
