from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Numeric, String, UniqueConstraint

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin


class MemberQuota(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}member_quota"
    __table_args__ = (
        UniqueConstraint("member_id", "cloud_provider_code", "quota_code", name="uq_member_quota"),
        {"comment": "会员已分配配额表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商编码")
    resource_type = Column(String(32), nullable=False, comment="资源类型编码")
    quota_name = Column(String(64), nullable=False, comment="配额名称")
    quota_code = Column(String(64), nullable=False, comment="配额编码")
    allocated_quota = Column(Numeric(18, 2), nullable=False, default=0, comment="已分配配额")
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
