from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin

from ...constants.enums import CloudImageStatus, BillingMethod

class CloudImage(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cloud_image"

    # 主键
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # === 镜像基础信息 ===
    image_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        comment="云厂商镜像ID"
    )

    image_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="镜像名称"
    )

    os_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="操作系统类型 linux/windows"
    )

    os_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="操作系统名称"
    )

    cloud_provider_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="厂商名称"
    )

    region_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="区域ID，如 cn-hangzhou、ap-southeast-1"
    )
    resource_group_id: Mapped[int] = mapped_column(Integer, nullable=True, comment="资源组")

    architecture: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="架构 x86_64/arm64"
    )

    boot_mode: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="启动固件模式：BIOS（传统启动） / UEFI（现代启动）,x86_64这2个都支持，arm64只支持UEFI"
    )

    size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="系统盘大小(GB)"
    )

    # === 业务字段 ===
    description: Mapped[str] = mapped_column(
        String(512),
        nullable=True,
        comment="镜像描述"
    )

    status: Mapped[CloudImageStatus] = mapped_column(
        SAEnum(CloudImageStatus),
        default=CloudImageStatus.AVAILABLE,
        nullable=False,
        comment="镜像状态，AVAILABLE=可用，DISABLED=禁用，DELETED删除"
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="所属用户ID，公共镜像可为空"
    )

    # === 计费 3 姐妹 ===
    charge_type: Mapped[BillingMethod] = mapped_column(
        SAEnum(BillingMethod),
        nullable=False,
        comment="计费类型 PrePaid=包年月/PostPaid=按量付费"
    )
    period: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="购买周期(月)，仅包年包月"
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否自动续费"
    )

    # price: Mapped[float] = mapped_column(
    #     Numeric(18, 2), nullable=False, comment="单价"
    # )

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