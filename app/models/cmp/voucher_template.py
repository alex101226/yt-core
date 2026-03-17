from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin


class VoucherTemplate(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}voucher_template"
    __table_args__ = {"comment": "代金券模板表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="模板ID")
    template_no = Column(String(64), unique=True, nullable=False, comment="模板编号")
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商编码")
    amount = Column(Numeric(18, 2), nullable=False, comment="面值金额")
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
