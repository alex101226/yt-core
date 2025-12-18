from sqlalchemy import Column, String, BigInteger, Float, Integer, DateTime, Enum, Boolean
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import CmpBase

class ProductOrder(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}product_order"
    __table_args__ = {"comment": "商品订单表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="订单主键ID")
    order_no = Column(String(64), unique=True, nullable=False, comment="订单号")
    instance_id = Column(String(64), nullable=True, comment="实例ID（创建的云资源ID）")
    product_id = Column(Integer, nullable=True, comment="产品id, 现在还没有，后面加")
    product_name = Column(String(64), nullable=False, comment="产品名称，如云服务器、裸金属等")
    item_name = Column(String(64), nullable=False, comment="商品名称，如带宽、CBS存储")
    order_type = Column(String(32), nullable=False, comment="订单类型：CREATE=新购/RENEW=续费/UPGRADE=升级/扩容订单")
    pay_status = Column(String(32), nullable=False, comment="支付状态：PENDING/SUCCESS/FAILED")
    consume_type = Column(String(32), nullable=False, comment="消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费")
    amount_payable = Column(Float, nullable=False, comment="应付金额")
    use_balance = Column(Float, default=0.0, comment="使用余额金额")
    use_coupon = Column(Boolean, default=False, comment="使用优惠券金额")
    use_voucher = Column(Boolean, default=False, comment="使用代金券金额")
    settlement_type = Column(String(32), nullable=False, comment="结算类型：PLATFORM=平台结算")
    cloud_vendor = Column(String(32), nullable=True, comment="云厂商")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="订单创建时间"
    )
    paid_at = Column(DateTime(timezone=True), nullable=True, comment="支付时间")
    account_id = Column(Integer, nullable=True, comment="关联账户ID")
