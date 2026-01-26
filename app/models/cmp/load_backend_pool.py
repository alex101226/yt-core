# 后端池
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

from ...constants.enums import LBAlgorithm, HealthCheckType


class BackendPool(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_backend_pool"
    __table_args__ = {'comment': '负载均衡后端池'}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="主键ID"
    )

    pool_id: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, comment="云厂商后端池ID"
    )

    listener_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="所属监听器ID"
    )

    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="后端池名称"
    )

    algorithm: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="调度算法"
    )

    health_check_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否开启健康检查"
    )

    health_check_protocol: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True, comment="健康检查协议"
    )

    health_check_path: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="HTTP(S)健康检查路径"
    )

    health_check_interval: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="健康检查间隔（秒）"
    )

    healthy_threshold: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="健康阈值"
    )

    unhealthy_threshold: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="不健康阈值"
    )

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="后端池状态"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间"
    )