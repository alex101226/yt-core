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
from app.schemas.cmp.account_schema import AccountRecharge, AccountCreate, FundsFlowCreate

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

    # 创建流水  datetime.now(timezone.utc).timestamp() * 1000
    def fund_data_create(self, data: FundsFlowCreate):
        funds_flow_db = self.repo.write_billing_flow(**data.model_dump())
        if not funds_flow_db:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return funds_flow_db

    # 充值
    def account_recharge(self, user_id, data: AccountCreate):
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
                account_data = {
                    "user_id": user_id,
                    "balance": diff_balance
                }
                account_db = self.repo.account_recharge(account_data)

                # 创建充值订单
                recharge_data = {
                    "user_id": user_id,
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
                    "user_id": user_id,
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
                }
                # funds_flow_db = self.repo.write_billing_flow(funds_flow_data)
                funds_flow_db = self.fund_data_create(FundsFlowCreate(**funds_flow_data))
                if not funds_flow_db:
                    raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
            return True
        except BusinessException as e:
            self.db.rollback()
            raise

    # 查询用户是否开通了账户
    def account_exists(self, user_id: int):
        result = self.repo.account_exists(user_id)
        if not result:
            return False
        return result

    # 加事务所的查询
    def account_recharge_exists(self, user_id: int):
        result = self.account_exists(user_id)
        if not result:
            return False
        return result

    # 创建商品订单
    def product_create(self, data: dict):
        product_payload = {
            **data,
            "pay_status": "PENDING",
            "order_no": f"EIP-{generate(size=10)}",
            "instance_id": data['instance_id'],
            "cloud_provider_code": data['cloud_provider_code'],
            "product_id": data['product_id'],
            "product_name": data['product_name'],
            "business_id": data['business_id'],
            "business_name": data['business_name'],
            "order_type": data['order_type'],
            "consume_type": data['consume_type'],  # 消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费
            "amount_payable": data['amount_payable'],
            "use_credit": data['use_credit'],
            "use_voucher": data['use_voucher'],
            "settlement_type": data['settlement_type'],
            "account_id": data['account_id'],
            "created_by":  data['created_by'],
            "charge_mode": data['charge_mode'],
        }
        # 创建订单
        product_result = self.repo.product_create(product_payload)
        if not product_result:
            raise BusinessException(code=ErrorCode.FAILED, message="订单创建失败")

        bill_payload = {
            "billing_period": data['billing_period'],
            "region": data['region'],
            "billing_item_name": data['billing_item_name'],
            "unit_price": data['price'],
            "unit": "HOUR",
            "duration": data['duration'],
            "coupon_amount": data['coupon_amount'],
            "credit_amount": data['credit_amount'],
            "balance_amount": data['price'],
            "voucher_amount": data['voucher_amount'],
            "owe_amount": data['owe_amount'],
            "order_id": product_result.id
        }
        # 创建订单明细
        bill_result = self.bill_details_create(bill_payload)
        return {
            **product_result,
            **bill_result,
        }

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
        self, account_balance: Decimal, data: dict):
        amount = Decimal(str(data['amount']))
        # 2. 计算余额    Decimal(str(eip.price))
        new_balance = (account_balance - amount).quantize(
            Decimal("0.00"),
            rounding=ROUND_HALF_UP
        )

        # 3. 更新账户余额
        # account.balance = new_balance
        self.repo.account_balance_update(new_balance, data['user_id'])

        # 创建流水  datetime.now(timezone.utc).timestamp() * 1000
        funds_flow_data = {
            **data,
            "balance_after": new_balance,
        }
        logger.info(f'查看传递来的信息 {funds_flow_data}')
        fund_result = self.fund_data_create(FundsFlowCreate(**funds_flow_data))
        return fund_result

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