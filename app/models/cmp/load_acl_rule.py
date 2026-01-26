from datetime import datetime, timezone
from sqlalchemy import Integer, String, Enum as SAEnum, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

from ...constants.enums import ACLStatus

class LoadBalancerACLRule(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_acl_rule"
    __table_args__ = {'comment': '负载均衡ACL规则'}

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="主键ID"
    )

    acl_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="ACL 策略ID"
    )

    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="源类型：IP / CIDR"
    )

    source_value: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="源地址，如 1.1.1.1 / 10.0.0.0/24"
    )

    description: Mapped[str] = mapped_column(
        String(512), nullable=True, comment="描述"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )

    #============== status，action，priority==================
    status: Mapped[ACLStatus] = mapped_column(
        SAEnum(ACLStatus), nullable=True, comment="规则状态"
    )

    action: Mapped[str] = mapped_column(
        String(10), nullable=True, comment="动作：ALLOW / DENY"
    )

    priority: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="优先级，数字越小优先级越高"
    )
