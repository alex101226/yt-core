from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, UniqueConstraint

from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin


class Studio(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}studio"
    __table_args__ = (
        UniqueConstraint("cluster_id", name="uq_studio_cluster_id"),
        UniqueConstraint("instance_id", name="uq_studio_instance_id"),
        {"comment": "AI Studio 业务实例表"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cluster_id = Column(Integer, nullable=False, comment="关联集群主键ID")
    studio_name = Column(String(128), nullable=False, comment="Studio名称")
    instance_id = Column(String(64), nullable=False, comment="Studio实例ID")
    studio_type = Column(String(32), nullable=False, default="基础版", comment="Studio类型")
    member_id = Column(Integer, nullable=True, comment="所属会员ID")
    resource_group_id = Column(String(64), nullable=True, comment="资源组ID")
    description = Column(String(255), nullable=True, comment="描述")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    status = Column(String(32), nullable=False, default="ENABLED", comment="Studio状态")
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
