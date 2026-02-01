from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin

class InvoiceEmail(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}invoice_email"
    __table_args__ = {'comment': '发票邮件表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), nullable=True, comment="操作用户ID")
    email =  Column(String(100), nullable=True, comment="邮件")
    is_default = Column(Boolean, nullable=False, comment="是否默认邮件")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )