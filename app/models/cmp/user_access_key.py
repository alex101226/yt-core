from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import CmpBase
from app.core.config import settings

from app.models.is_released_mixin import IsReleasedMixin

class UserAccessKey(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}user_access_key"
    __table_args__ = {"comment": "AccessKey 表"}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    # ===== 云厂商 =====
    cloud_provider_code: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="云厂商 code，如 aliyun / aws / tencent"
    )

    # ===== AccessKey =====
    access_key_id: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="AccessKey ID"
    )
    access_key_secret: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="AccessKey Secret（建议加密存储）"
    )

    # ===== 状态 =====
    status: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="状态：1=启用，0=禁用"
    )

    # ===== 使用访问时间 =====
    last_visit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最近一次访问时间"
    )

    # ===== 审计 =====
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
