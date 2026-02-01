# models/account_funds_flow.py
import enum
from sqlalchemy import Column, BigInteger, Numeric, String, DateTime, Integer, Enum
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import CmpBase

from app.models.is_released_mixin import IsReleasedMixin
from app.constants.enums import (
Direction,FundType,RefType,Channel, FlowType
)


class FundsFlow(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}account_funds_flow"
    __table_args__ = {"comment": "用户资金流水表"}

    # 基本标识
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="流水ID")
    account_id = Column(Integer, nullable=False, comment="资金账户ID")
    flow_no = Column(String(64), unique=True, nullable=False, comment="流水号（对外展示）")

    # 资金维度
    direction = Column(Enum(Direction), nullable=False, comment="方向：IN/OUT")
    flow_type = Column(Enum(FlowType), nullable=False, comment="流水类型：RECHARGE/PAY_ORDER/REFUND等")
    fund_type = Column(Enum(FundType), nullable=False, comment="资金形式：BALANCE/CREDIT/VOUCHER")
    amount = Column(Numeric(18, 2), nullable=False, comment="变动金额，正为增加，负为扣减")
    balance_after = Column(Numeric(18, 2), nullable=False, comment="变动后的账户余额")

    # 关联业务
    ref_type = Column(Enum(RefType), nullable=False, comment="关联业务类型：充值订单/消费订单/账单明细/退款订单")
    ref_id = Column(BigInteger, comment="关联业务对象ID，例如 recharge_order.id 或 order.id")
    billing_period = Column(String(32), nullable=True, comment="账期（YYYY-MM），按月汇总使用")

    # 渠道和操作
    channel = Column(Enum(Channel), nullable=True, comment="交易渠道：USER_ACCOUNT/ALIPAY/WECHAT/SYSTEM")
    third_trade_no = Column(String(64), nullable=True, comment="第三方流水号")
    description = Column(String(255), nullable=True, comment="交易备注或说明")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")