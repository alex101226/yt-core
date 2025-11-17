from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.config import settings
from app.core.database import PublicBase


class ResourceGroup(PublicBase):
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}resource_group"
    __table_args__ = ({"comment": "资源组信息表"})

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="资源组名称（阿里云的 DisplayName）")
    code = Column(String(100), nullable=True, comment="系统内部资源组编码，可选")

    description = Column(Text, nullable=True, comment="描述信息")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间 (UTC)",
    )

    bindings = relationship("ResourceGroupBinding", back_populates="group", cascade="all, delete-orphan")


class ResourceGroupBinding(PublicBase):
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}resource_group_binding"
    __table_args__ = (
        UniqueConstraint("cloud_provider_code", "resource_type", "resource_id", name="uq_rg_resource"),
        {"comment": "资源与资源组的绑定表"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resource_group_id = Column(
        Integer,
        ForeignKey(f"{settings.PUBLIC_TABLE_PREFIX}resource_group.id", ondelete="CASCADE"),
        nullable=False,
        comment="资源组 ID",
    )
    cloud_provider_code = Column(String(50), nullable=True, comment="云厂商，如 aliyun")

    resource_type = Column(String(100), nullable=False, comment="资源类型，例如 ecs/vpc/bucket/subsystem_xxx")
    # resource_id = 云资源在系统内部的唯一ID（不是DB自增ID，而是业务ID，云资源的真实ID）
    resource_id = Column(String(200), nullable=False, comment="资源在系统内的唯一 ID")
    resource_name = Column(String(200), nullable=True, comment="资源名称（冗余存储，避免每次查云资源表）")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="绑定时间 (UTC)",
    )

    group = relationship("ResourceGroup", back_populates="bindings")
