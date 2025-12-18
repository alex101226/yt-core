# models/billing_flow.py
from sqlalchemy import Column, BigInteger, Numeric, String, DateTime, Integer
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import CmpBase


class BillingFlow(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}billing_flow"
    __table_args__ = {"comment": "用户资金流水表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="流水ID")
    user_id = Column(Integer, nullable=False, comment="关联用户ID")

    flow_type = Column(String(32), nullable=False, comment="流水类型：RECHARGE/PAY_ORDER/REFUND等")
    amount = Column(Numeric(18, 2), nullable=False, comment="变动金额，正为增加，负为扣减")
    balance_after = Column(Numeric(18, 2), nullable=False, comment="变动后的账户余额")

    ref_type = Column(String(32), comment="关联业务类型：充值订单(RECHARGE)、消费订单(PAY_ORDER)、优惠券(COUPON)等")
    ref_id = Column(BigInteger, comment="关联业务对象ID，例如 recharge_order.id 或 order.id")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
