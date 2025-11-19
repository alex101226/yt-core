# app/models/cmp/security_group_rule.py

from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, DateTime,
    ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from app.core.database import CmpBase
from app.core.config import settings

#   安全组规则表（入方向 / 出方向规则）
class SecurityGroupRule(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}security_group_rule"
    __table_args__ = {"comment": "安全组规则表"}

    # 主键 ID（UUID）
    id = Column(String(36), primary_key=True, index=True, comment="主键ID")

    # 所属安全组 ID
    security_group_id = Column(
        String(36),
        ForeignKey("cm_security_group.id"),
        nullable=False,
        index=True,
        comment="所属安全组ID，关联 cm_security_group.id"
    )

    # 方向：inbound / outbound
    direction = Column(
        String(20),
        nullable=False,
        comment="规则方向：inbound（入方向）/ outbound（出方向）"
    )

    # 策略：accept / drop
    policy_code = Column(
        String(50),
        nullable=False,
        comment="策略字典项编码，如：ALLOW / DENY"
    )

    # 协议类型（字典项 item_code）
    protocol_code = Column(
        String(50),
        nullable=False,
        comment="协议类型字典项编码，如：CUSTOM_TCP / CUSTOM_UDP / ICMP_ALL"
    )

    # 端口范围，例如：22/22、80/80、1/65535
    port_range = Column(
        String(50),
        nullable=False,
        comment="端口范围，如：22/22、80/80、1/65535"
    )

    # 来源 CIDR（入方向）或 目标 CIDR（出方向）
    source = Column(
        String(100),
        nullable=False,
        comment="CIDR：入方向为来源CIDR，出方向为目标CIDR"
    )

    # 规则描述
    description = Column(
        String(255),
        nullable=True,
        comment="规则描述信息"
    )

    # 云端规则 ID（不同云是否支持不一致，可为空）
    cloud_rule_id = Column(
        String(100),
        nullable=True,
        comment="云端规则ID（如果云厂商支持）"
    )

    # 同步状态：0未同步，1已同步，2待更新，3删除中
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

    # 关联安全组
    security_group = relationship("SecurityGroup", back_populates="rules")
