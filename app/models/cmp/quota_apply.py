from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Numeric, String

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin


class QuotaApply(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}quota_apply"
    __table_args__ = {"comment": "配额申请审批表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商编码")
    resource_type = Column(String(32), nullable=False, comment="资源类型编码")
    quota_name = Column(String(64), nullable=False, comment="配额名称")
    quota_code = Column(String(64), nullable=False, comment="配额编码")
    quantity_type = Column(String(32), nullable=False, comment="数量类型")
    allocated_quota = Column(Numeric(18, 2), nullable=False, default=0, comment="当前分配配额")
    apply_quota = Column(Numeric(18, 2), nullable=False, comment="申请配额")
    apply_remark = Column(String(255), nullable=True, comment="申请备注")
    approve_status = Column(String(32), nullable=False, default="PENDING", comment="审批状态")
    approved_by = Column(Integer, nullable=True, comment="审批人ID")
    approved_by_name = Column(String(60), nullable=True, comment="审批人")
    approve_remark = Column(String(255), nullable=True, comment="审批备注")
    approved_at = Column(DateTime(timezone=True), nullable=True, comment="审批时间(UTC)")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间(UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间(UTC)",
    )
