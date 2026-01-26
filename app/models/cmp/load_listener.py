#   监听器

# id
# instance_id
# protocol              # HTTP / HTTPS / TCP
# port
# load_balance_policy   # RR / WEIGHT / IP_HASH
# session_sticky        # on / off
# status
# certificate_id        # nullable
# acl_id                # nullable
# created_at
# updated_at

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Integer, String, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

from ...constants.enums import ListenerProtocol, ListenerStatus


class LoadBalancerListener(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_listener"
    __table_args__ = {'comment': '负载均监听器'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    listener_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="云厂商监听器ID")

    lb_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="所属负载均衡实例ID")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="监听器名称")

    protocol: Mapped[ListenerProtocol] = mapped_column(
        SAEnum(ListenerProtocol), nullable=False, comment="监听协议"
    )
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment="监听端口")
    backend_port: Mapped[int] = mapped_column(Integer, nullable=False, comment="后端端口")

    status: Mapped[ListenerStatus] = mapped_column(
        SAEnum(ListenerStatus), nullable=False, comment="监听器状态"
    )

    user_id: Mapped[int] = mapped_column(Integer, nullable=False, comment="创建用户ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )
