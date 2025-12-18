from sqlalchemy import Column, String, BigInteger, Float, Integer, DateTime, Enum
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import CmpBase

class BillingDetail(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}billing_detail"
    __table_args__ = {"comment": "账单明细表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="明细账单ID")
    instance_id = Column(String(64), nullable=False, comment="实例ID")
    billing_period = Column(String(32), nullable=False, comment="账期，例如2025-12")
    product_name = Column(String(64), nullable=False, comment="产品名称")
    item_name = Column(String(64), nullable=False, comment="商品名称")
    consume_type = Column(String(32), nullable=False, comment="消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费")
    cloud_vendor = Column(String(32), nullable=True, comment="云厂商")
    settlement_type = Column(String(32), nullable=False, comment="结算类型：PLATFORM=平台结算")
    region = Column(String(32), nullable=True, comment="区域")
    billing_item_name = Column(String(64), nullable=False, comment="计费项名称")
    unit_price = Column(Float, nullable=False, comment="单价")
    unit = Column(String(32), nullable=True, comment="单价单位")
    duration = Column(Float, nullable=True, comment="服务时长")
    discount_amount = Column(Float, default=0.0, comment="优惠金额")
    payable_amount = Column(Float, nullable=False, comment="应付金额")
    coupon_amount = Column(Float, default=0.0, comment="代金券支付金额")
    low_commission_amount = Column(Float, default=0.0, comment="抵用金支付金额")
    owe_amount = Column(Float, default=0.0, comment="欠费金额")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="明细账单生成时间"
    )
