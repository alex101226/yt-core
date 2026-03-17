from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin


class CreditGrant(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}credit_grant"
    __table_args__ = {"comment": "低佣金发放记录表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="发放ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    amount = Column(Numeric(18, 2), nullable=False, comment="发放金额")
    remaining_amount = Column(Numeric(18, 2), nullable=False, comment="剩余金额")
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商编码")
    valid_start = Column(DateTime(timezone=True), nullable=False, comment="生效开始时间(UTC)")
    valid_end = Column(DateTime(timezone=True), nullable=False, comment="生效结束时间(UTC)")
    status = Column(String(32), nullable=False, default="ACTIVE", comment="状态：ACTIVE/EXPIRED/USED_UP/CANCELLED")
    source_type = Column(String(32), nullable=False, default="INTERNAL", comment="来源类型：INTERNAL")
    description = Column(String(255), nullable=True, comment="描述/备注")
    approve_status = Column(String(32), nullable=False, default="PENDING", comment="审批状态：PENDING/APPROVED/REJECTED")
    approved_by = Column(Integer, nullable=True, comment="审批人id")
    approved_by_name = Column(String(60), nullable=True, comment="审批人信息")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审批时间(UTC)")
    reject_reason = Column(String(255), nullable=True, comment="驳回原因")

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
