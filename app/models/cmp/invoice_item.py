from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from sqlalchemy import (
    String,
    Integer,
    DateTime,
    Numeric,
    Enum as SAEnum,
    ColumnElement,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings

from app.models.is_released_mixin import IsReleasedMixin
from ...constants.enums import InvoiceItemStatus


class InvoiceItem(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}invoice_item"
    __table_args__ = {"comment": "开具发票表"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ===== 账期 =====
    billing_period: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="账期，如 2026-01"
    )
    billing_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    billing_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # ===== 开票主体（云厂商）=====
    cloud_provider_code: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="云厂商 code，如 aws / aliyun / tencent"
    )
    cloud_provider_name: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="云厂商名称"
    )

    # ===== 业务属性 =====  # 订单类型：CREATE=新购/RENEW=续费/UPGRADE=升级/扩容订单
    order_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="下单类型：CREATE=新购/RENEW=续费/UPGRADE=升级/扩容订单"
    )
    target_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="开票对象类型：BILL(账单)"
    )
    product_display_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="产品展示名称（发票用）"
    )

    # ===== 订单关联 =====
    origin_order_no: Mapped[str] = mapped_column(
        String(64), nullable=True, comment="原始订单号"
    )
    instance_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="实例 ID（可为空）"
    )

    # ===== 金额 =====
    paid_amount: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, comment="订单实付金额"
    )
    invoice_amount: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=False, comment="可开票金额"
    )
    issued_amount: Mapped[float] = mapped_column(
        Numeric(18, 2), nullable=True, comment="已开票金额"
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, default="CNY"
    )

    # ===== 时间 =====
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="订单支付时间"
    )
    issued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开票时间"
    )

    # ===== 发票关联 =====
    invoice_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="已开票后关联的发票 ID",
    )

    # ===== 状态 =====
    status: Mapped[InvoiceItemStatus] = mapped_column(
        SAEnum(InvoiceItemStatus),
        nullable=False,
        default=InvoiceItemStatus.UNISSUED,
        comment="UNISSUED=未开票，ISSUED=已开票",
    )

    # ===== 审计 =====
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # =============================
    # 业务属性（不入库）
    # =============================

    @property
    def is_overdue(self) -> Union[bool, ColumnElement[bool]]:
        """
        是否欠票（默认 30 天）
        """
        if self.status != InvoiceItemStatus.UNISSUED:
            return False
        return self.paid_at < datetime.now(timezone.utc) - timedelta(days=30 * 6)
