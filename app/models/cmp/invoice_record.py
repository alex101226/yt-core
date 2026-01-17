from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings

from .is_released_mixin import IsReleasedMixin

from ...constants.enums import InvoiceRecordType, InvoiceRecordStatus

# ------------------------
# 发票 Model
# ------------------------
class InvoiceRecord(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}invoice_record"
    __table_args__ = {"comment": "已开的发票记录"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 用户
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 被开票的 InvoiceItem ID 列表，前端传 string[]，数据库用 JSON 存储
    invoice_item_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment="被开票的记录ID列表")

    invoice_type: Mapped[InvoiceRecordType] = mapped_column(Enum(InvoiceRecordType), nullable=False, comment="发票类型")
    invoice_no = mapped_column(String(64), nullable=True, comment="发票号（第三方返回）")

    invoice_item_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="发票抬头ID")
    email: Mapped[str] = mapped_column(String(255), nullable=False, comment="电子邮箱")
    remark: Mapped[str] = mapped_column(String(500), nullable=True, comment="用户备注")

    amount: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False, comment="开票金额总计")

    status: Mapped[InvoiceRecordStatus] = mapped_column(Enum(InvoiceRecordStatus), default=InvoiceRecordStatus.ISSUED, comment="发票记录状态")

    issued_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开票时间"
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
