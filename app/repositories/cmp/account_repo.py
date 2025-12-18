from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.account import Account
from app.models.cmp.recharge_order import RechargeOrder
from app.models.cmp.billing_flow import BillingFlow
from app.models.cmp.product_order import ProductOrder
from app.models.cmp.billing_detail import BillingDetail

class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    # 开通账户
    def account_create(self, data: dict):
        account = Account(**data)
        self.db.add(account)
        self.db.flush()
        self.db.commit()
        return account


    # 充值
    def account_recharge(self, data: dict):
       account = self.account_exists(data['user_id'])
       if not account:
           return None
       account.balance = data['balance']
       self.db.flush()
       return account

    # 充值
    def write_charge(self, data: dict):
        recharge = RechargeOrder(**data)
        self.db.add(recharge)
        self.db.flush()
        self.db.commit()
        return recharge

    # 写入流水
    def write_billing_flow(self, data: dict):
        billing_flow = BillingFlow(**data)
        self.db.add(billing_flow)
        self.db.flush()
        self.db.commit()
        return billing_flow


    # 查询用户是否开通了账户   .with_for_update()
    def account_exists(self, user_id: int):
        return self.db.query(Account).filter(Account.user_id == user_id).first()

    # 用户充值查看账户信息
    def account_recharge_find(self, user_id: int):
        return self.db.query(Account).filter(Account.user_id == user_id).with_for_update().first()