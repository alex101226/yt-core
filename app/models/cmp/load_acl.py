#   访问控制
from datetime import datetime, timezone
from sqlalchemy import Integer, String, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin

from ...constants.enums import ACLStatus


class LoadBalancerACL(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_acl"
    __table_args__ = {'comment': '负载均衡访问控制'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    acl_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="ACL 名称")

    # 归属信息
    resource_group_id: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="资源组ID"
    )
    cloud_provider_code: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="云厂商编码"
    )
    region_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="区域ID"
    )


    source_cidr: Mapped[str] = mapped_column(String(255), nullable=False, comment="源地址CIDR列表")

    description: Mapped[str] = mapped_column(
        String(512), nullable=True, comment="描述"
    )
    status: Mapped[ACLStatus] = mapped_column(
        SAEnum(ACLStatus), nullable=False, comment="ACL 状态"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )