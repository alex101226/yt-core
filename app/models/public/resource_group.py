# resource_group.py — SQLAlchemy Models (Public Service DB)
# ------------------------------------------------------------
# This defines the ResourceGroup and ResourceGroupBinding models
# built on top of your existing PublicBase.

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
    __table_args__ = (
        UniqueConstraint("cloud_provider_code", "cloud_resource_group_id", name="uq_cloud_rg"),
        {"comment": "资源组信息表"},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="资源组名称（阿里云的 DisplayName）")
    code = Column(String(100), nullable=True, comment="系统内部资源组编码，可选")
    cloud_provider_code = Column(String(50), nullable=True, comment="云厂商编码，例如 aliyun")
    cloud_resource_group_id = Column(String(200), nullable=True, comment="云厂商的资源组ID，例如 rg-acfmx1234****")

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
    resource_id = Column(String(200), nullable=False, comment="资源在系统内的唯一 ID")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="绑定时间 (UTC)",
    )

    group = relationship("ResourceGroup", back_populates="bindings")


# 你可以直接运行 alembic -c alembic/public/alembic.ini revision --autogenerate -m "create resource group tables"
# 然后 upgrade 即可生成对应的两张表。
