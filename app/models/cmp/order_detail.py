from sqlalchemy import Column, String, BigInteger, Float, Integer, DateTime, Enum, Boolean
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import CmpBase

class OrderDetail(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}product_order_detail"
    __table_args__ = {"comment": "商品订单明细表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="明细账单ID")
    order_id = Column(BigInteger, index=True, nullable=False, comment="商品订单id")

    billing_period = Column(String(32), nullable=False, comment="账期，例如2025-12")
    region = Column(String(32), nullable=True, comment="区域")
    billing_item_name = Column(String(64), nullable=False, comment="计费项名称")
    unit_price = Column(Float, nullable=False, comment="单价")
    unit = Column(String(32), nullable=True, comment="单价单位")
    duration = Column(Float, nullable=True, comment="服务时长")
    coupon_amount = Column(Float, default=0.0, comment="优惠金额")
    credit_amount = Column(Float, default=0.0, comment="抵用金支付金额")
    voucher_amount = Column(Float, default=0.0, comment="代金券支付金额")
    balance_amount = Column(Float, default=0, comment="使用余额金额")
    owe_amount = Column(Float, default=0.0, comment="欠费金额")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="明细账单生成时间"
    )
