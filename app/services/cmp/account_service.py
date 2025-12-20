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
            "amount": +amount,
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

    # 创建商品订单
    def product_create(self, data: dict):
        product_order = self.repo.product_create(data)
        if not product_order:
            raise BusinessException(code=ErrorCode.FAILED, message="订单创建失败")
        return product_order

    # 创建账单明细
    def bill_details_create(self, data: dict):
        billing_detail = self.repo.bill_details_create(data)
        if not billing_detail:
            raise BusinessException(code=ErrorCode.FAILED, message="账单明细创建失败")
        return billing_detail

    # 查找订单是否存在
    def get_last_product_order(self, instance_id: str):
        return self.repo.get_last_product_order(instance_id)

    # 统一扣费入口
    def pay(
        self, *, user_id: int, amount: Decimal, flow_type: str, ref_type: str, ref_id: int
    ):
        # 1. 锁账户
        account = self.repo.account_recharge_find(user_id)
        if not account:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="账户不存在")

        amount = Decimal(str(amount))
        # 2. 计算余额    Decimal(str(eip.price))
        new_balance = (account.balance - amount).quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP
        )

        # 3. 更新账户余额
        account.balance = new_balance

        # 4. 写资金流水  流水类型：RECHARGE/PAY_ORDER/REFUND等
        bill_flow = self.repo.write_billing_flow({
            "user_id": user_id,
            "flow_type": flow_type,  # PAY_ORDER
            "amount": -amount,  # 负数
            "balance_after": new_balance,
            "ref_type": ref_type,  # PRODUCT_ORDER
            "ref_id": ref_id
        })
        # if not bill_flow:
        #     raise BusinessException(code=ErrorCode.FAILED, message="流水创建失败")
        return bill_flow

    # 其他资源（ECS / 磁盘）——立即扣费
    def pay_immediately(self, user_id: int, amount: Decimal, product_info: dict):
        # 1. 创建商品订单
        order = self.repo.product_create({
            **product_info,
            "pay_status": "SUCCESS"
        })

        # 2. 扣费
        self.account_service.pay(
            user_id=user_id,
            amount=amount,
            flow_type="PAY_ORDER",
            ref_type="PRODUCT_ORDER",
            ref_id=order.id
        )

        return order