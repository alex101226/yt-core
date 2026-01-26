#   模型成员

# 用户请求
# ↓
# service_address（Instance）
# ↓
# Listener（端口 / 协议）
# ↓
# ACL 判断（允许 / 拒绝）
# ↓
# BackendPool
# ↓
# BackendMember（IP:Port）

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

from ...constants.enums import BackendStatus


class BackendMember(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_backend_member"
    __table_args__ = {'comment': '负载均衡后端成员'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    listener_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="所属监听器ID")

    resource_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="后端资源类型(server/cluster_node)")
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="后端资源ID")

    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, comment="后端IP地址")
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="后端服务端口")
    weight: Mapped[int] = mapped_column(Integer, default=100, comment="转发权重")

    status: Mapped[BackendStatus] = mapped_column(
        SAEnum(BackendStatus), nullable=False, comment="后端实例状态"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )
