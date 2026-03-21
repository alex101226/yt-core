from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.account import Account
from app.models.cmp.order_recharge import RechargeOrder
from app.models.cmp.account_funds_flow import FundsFlow
# from app.models.cmp.order import ProductOrder
# from app.models.cmp.order_detail import ProductOrderDetail

class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    # 开通账户
    def account_create(self, data: dict):
        account = Account(**data)
        self.db.add(account)
        # self.db.flush()
        self.db.commit()
        self.db.refresh(account)
        return account

    # 删除账户
    def account_delete(self, user_id: int):
        find = self.account_exists(user_id)
        if not find:
            return None
        find.is_released = True
        self.db.commit()
        self.db.refresh(find)
        return find

    # 充值
    def account_recharge(self, data: dict):
       account = self.account_exists(data['user_id'])
       if not account:
           return None
       account.balance = data['balance']
       self.db.flush()
       return account

    # 写入充值订单
    def write_charge(self, data: dict):
        recharge = RechargeOrder(**data)
        self.db.add(recharge)
        self.db.flush()
        return recharge

    # 写入流水
    def write_billing_flow(self, **kwargs):
        billing_flow = FundsFlow(**kwargs)
        self.db.add(billing_flow)
        self.db.flush()
        return billing_flow

    # 查询用户是否开通了账户
    def account_exists(self, user_id: int):
        return self.db.query(Account).filter(Account.created_by == user_id).first()

    def get_by_id(self, account_id: int):
        return self.db.query(Account).filter(Account.id == account_id).first()

    # 更新用户的账户余额
    def account_balance_update(self, amount: Decimal, user_id: int):
        account = self.account_exists(user_id)
        if not account:
            return None
        account.balance = amount
        self.db.flush()
        return account

    # 用户充值查看账户信息
    def account_recharge_find(self, user_id: int):
        return self.db.query(Account).filter(Account.created_by == user_id).with_for_update().first()
