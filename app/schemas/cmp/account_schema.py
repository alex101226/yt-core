from decimal import Decimal
from pydantic import BaseModel
from typing import Optional, List

class AccountRecharge(BaseModel):
    balance: float

class AccountCreate(BaseModel):
    pay_channel: str
    amount: Decimal
