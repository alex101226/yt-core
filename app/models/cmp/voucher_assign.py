from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin


class VoucherAssign(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}voucher_assign"
    __table_args__ = {"comment": "代金券分配表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分配ID")
    template_id = Column(Integer, nullable=False, comment="模板ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    valid_start = Column(DateTime(timezone=True), nullable=False, comment="生效开始时间")
    valid_end = Column(DateTime(timezone=True), nullable=False, comment="生效结束时间")
    quantity = Column(Integer, nullable=False, comment="份数")
    remaining_amount = Column(Numeric(18, 2), nullable=False, default=0, comment="剩余可抵扣金额")
    description = Column(String(255), nullable=True, comment="描述/备注")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间(UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间(UTC)"
    )
