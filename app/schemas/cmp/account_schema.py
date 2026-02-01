from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List

class AccountRecharge(BaseModel):
    balance: float

# 资金账户创建
class AccountCreate(BaseModel):
    pay_channel: str
    amount: Decimal


# 资金流水基础信息
class FundsFlowBase(BaseModel):
    account_id: int
    flow_no: str
    third_trade_no: str
    channel: str
    direction: str
    flow_type: str
    fund_type: str
    ref_type: str
    ref_id: int
    billing_period: str
    amount: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    created_by: int
    created_by_name: str

# 资金流水创建
class FundsFlowCreate(FundsFlowBase):
    pass

