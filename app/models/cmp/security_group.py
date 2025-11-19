# app/models/cmp/security_group.py
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, JSON,
    ForeignKey, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.database import CmpBase
from app.core.config import settings

class SecurityGroup(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}security_group"
    __table_args__ = {"comment": "安全组主表"}

    id = Column(String(36), primary_key=True, index=True, comment="安全组本地唯一 ID")
    security_name = Column(String(100), nullable=False, comment="安全组名称")
    description = Column(Text, nullable=True, comment="安全组描述")
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    cloud_certificate_id = Column(Integer, nullable=False, comment="云凭证ID")
    region_id = Column(String(50), nullable=False, comment="区域 ID，例如 cn-beijing")
    # CMP 内部表，可以做外键
    vpc_id = Column(
        Integer(),
        ForeignKey(f"{settings.CMP_TABLE_PREFIX}vpc.id"),
        nullable=False,
        comment="本地 VPC 表 id"
    )
    cloud_group_id = Column(String(100), unique=True, nullable=True, comment="云端安全组 ID（sg-xxxx）")
    sync_status = Column(
        Integer,
        default=0,
        comment="同步状态：0未同步，1已同步，2待更新，3删除中"
    )
    # 释放字段
    is_released = Column(Boolean, default=False, nullable=False, comment="是否已释放")
    released_at = Column(DateTime(timezone=True), nullable=True, comment="释放时间 (UTC)")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False,
        comment="创建时间 (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False, comment="更新时间 (UTC)"
    )
    # CMP 内部关联的规则
    rules = relationship("SecurityGroupRule", back_populates="security_group", cascade="all, delete-orphan")
    # vpc 内部关联
    vpc = relationship("Vpc", lazy="joined")
