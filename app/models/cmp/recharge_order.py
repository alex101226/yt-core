# models/recharge_order.py
from sqlalchemy import Column, BigInteger, Numeric, String, DateTime, Enum, Integer
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings
import enum


class PayChannel(str, enum.Enum):
    ALIPAY = "ALIPAY" # 支付宝
    WECHAT = "WECHAT" # 微信
    BANK = "BANK" # 银行转账


class PayStatus(str, enum.Enum):
    PENDING = "PENDING" # 待支付
    SUCCESS = "SUCCESS" # 支付成功
    FAILED = "FAILED" # 支付失败

class RechargeOrder(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}recharge_order"
    __table_args__ = {"comment": "用户现金账户表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="充值订单ID")
    user_id = Column(Integer, nullable=False, comment="关联用户ID")
    account_id = Column(Integer, nullable=False, comment="资金账户ID")

    amount = Column(Numeric(18, 2), nullable=False, comment="充值金额")

    pay_channel = Column(Enum(PayChannel), default=PayChannel.ALIPAY, comment="支付渠道：支付宝/微信/银行卡")

    status = Column(Enum(PayStatus), nullable=False, default=PayStatus.SUCCESS, comment="订单状态")

    channel_trade_no = Column(String(64), unique=True, nullable=False, comment="平台生成的支付单号，用于幂等")
    third_trade_no = Column(String(64), comment="第三方支付交易号")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
    paid_at = Column(DateTime(timezone=True), comment="支付完成时间")

