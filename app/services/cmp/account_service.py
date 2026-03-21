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
from app.repositories.cmp.bill_repo import BillRepository
from app.schemas.cmp.account_schema import AccountRecharge, AccountCreate, FundsFlowCreate

class AccountService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AccountRepository(db)
        self.bill_repo = BillRepository(db)

    # 开通账户
    def account_create(self, new_user):
        is_account = self.account_exists(new_user.id)
        if is_account:
            raise BusinessException(code=ErrorCode.FAILED, message="账户已存在，请勿重复创建")

        payload = {
            "created_by": new_user.id,
            "created_by_name": new_user.username,
            "balance": 0.00,
            "account_name": new_user.nickname,
            "account_type": "PERSONAL",
            "account_status": "ACTIVE"
        }
        account = self.repo.account_create(payload)
        if not account:
            raise BusinessException(code=ErrorCode.FAILED, message="创建失败")
        return True

    # 创建流水  datetime.now(timezone.utc).timestamp() * 1000
    def fund_data_create(self, data: FundsFlowCreate):
        funds_flow_db = self.repo.write_billing_flow(**data.model_dump())
        if not funds_flow_db:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return funds_flow_db

    # 充值
    def account_recharge(self, user: dict, data: AccountCreate):
        user_id = user["user_id"]
        try:
            with self.db.begin():
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
                account_data = {"user_id": user_id, "balance": diff_balance }
                account_db = self.repo.account_recharge(account_data)

                # 创建充值订单
                recharge_data = {
                    "created_by": user_id,
                    "created_by_name": user['username'],
                    "account_id": account_db.id,
                    "amount": +amount,
                    "pay_channel": data.pay_channel or "ALIPAY",
                    "status": "SUCCESS",
                    "channel_trade_no": f"cmp-charge-{generate(size=6)}",
                    "third_trade_no": f"{data.pay_channel}-charge-{generate(size=6)}",
                    "paid_at": datetime.now(timezone.utc),
                }
                recharge_db = self.repo.write_charge(recharge_data)

                # 创建流水  datetime.now(timezone.utc).timestamp() * 1000
                funds_flow_data = {
                    "account_id": account_db.id,
                    "flow_no": f"{datetime.now(timezone.utc).timestamp() * 1000}{recharge_db.id % 1000:03d}",
                    "direction": "IN",
                    "flow_type": "RECHARGE",
                    "fund_type": "BALANCE",
                    "amount": data.amount,
                    "balance_after": account_db.balance,
                    "ref_type": "RECHARGE_ORDER",
                    "ref_id": recharge_db.id,
                    "billing_period": datetime.now().strftime("%Y-%m"),
                    "channel": "ALIPAY",
                    "third_trade_no": recharge_db.third_trade_no,
                    "description": "ALIPAY 充值平台账户",
                    "created_by": user_id,
                    "created_by_name": user['username'],
                }

                funds_flow_db = self.fund_data_create(FundsFlowCreate(**funds_flow_data))
                if not funds_flow_db:
                    raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
                # 仅当欠费清零后，才恢复计费任务
                if account_db.balance >= 0:
                    self.bill_repo.resume_by_user(user_id)
            return True
        except BusinessException as e:
            self.db.rollback()
            raise

    # 查询用户是否开通了账户
    def account_exists(self, user_id: int):
        result = self.repo.account_exists(user_id)
        if not result:
            return None
        return result

    def owner_account_exists(self, user: dict):
        user_id = user.get("user_id")
        parent_id = user.get("parent_id") or 0
        owner_user_id = user_id if parent_id == 0 else parent_id
        return self.account_exists(owner_user_id)

    # 删除账户
    def account_delete(self, user_id: int):
        find = self.repo.account_delete(user_id)
        return find

    # 加事务所的查询
    def account_recharge_exists(self, user_id: int):
        result = self.account_exists(user_id)
        if not result:
            return False
        return result

    # 统一扣费入口
    def pay(self, data: dict):
        account = self.repo.account_exists(data['created_by'])

        # 2. 计算余额
        new_balance = (account.balance - data['amount']).quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP
        )

        # 3. 更新账户余额
        self.repo.account_balance_update(new_balance, data['created_by'])

        # 创建流水  datetime.now(timezone.utc).timestamp() * 1000
        funds_flow_data = {
            **data,
            "balance_after": new_balance,
        }

        fund_result = self.fund_data_create(FundsFlowCreate(**funds_flow_data))

        # 4. 余额低于阈值则暂停用户所有计费任务
        if new_balance <= -5000:
            self.bill_repo.suspend_by_user(data['created_by'])
        return fund_result
