from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.repositories.cmp.account_repo import AccountRepository
from app.schemas.cmp.account_schema import AccountRecharge, AccountCreate

class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRepository(db)

    # 开通账户
    def account_create(self, user_id: int):
        is_account = self.account_exists(user_id)
        if is_account:
            raise BusinessException(code=ErrorCode.FAILED, message="账户已存在，请勿重复创建")

        payload = {
            "user_id": user_id,
            "balance": 0.00
        }
        account = self.repo.account_create(payload)
        if not account:
            raise BusinessException(code=ErrorCode.FAILED, message="创建失败")
        return True

    # 充值
    def account_recharge(self, user_id, data: AccountCreate):
        # 查看用户是否存在账户,这里有用户的余额信息
        user_balance = self.repo.account_recharge_find(user_id)
        if not user_balance:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        amount = Decimal(str(data.amount))
        diff_balance = (user_balance.balance + amount).quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP
        )
        # 账户余额信息
        account = {
            "user_id": user_id,
            "balance": diff_balance
        }
        account_db = self.repo.account_recharge(account)

        recharge = {
            "user_id": user_id,
            "amount": amount,
            "pay_channel": data.pay_channel or "ALIPAY",
            "status": "SUCCESS",
            "channel_trade_no": f"cmp-charge-{generate(size=6)}",
            "third_trade_no": f"{data.pay_channel}-charge-{generate(size=6)}",
        }
        recharge_db = self.repo.write_charge(recharge)

        billing_flow = {
            "user_id": user_id,
            "flow_type": "RECHARGE",
            "amount": data.amount,
            "balance_after": account_db.balance,
            "ref_type": data.pay_channel,
            "ref_id": recharge_db.id,
        }
        billing_flow_db = self.repo.write_billing_flow(billing_flow)
        if not billing_flow_db:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)

        self.db.commit()
        return True

    # 查询用户是否开通了账户
    def account_exists(self, user_id: int):
        result = self.repo.account_exists(user_id)
        if not result:
            return False
        return result