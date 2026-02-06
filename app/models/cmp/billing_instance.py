# app/models/cmp/billing_instance.py
from sqlalchemy import Column, DateTime, BigInteger, DECIMAL, Boolean, UniqueConstraint, Index, Enum, String, Integer
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

from app.models.is_released_mixin import IsReleasedMixin
from app.constants.enums import (
BillingCycle, BillingStatus, ResourceType, BillingMethod
)

"""
计费任务
用于记录实例创建过程中产生的价格计算、扣费流程
"""
class BillingInstance(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}billing_instance"
    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            name="uk_resource_type_id"
        ),
        Index("ix_billing_status", "status"),
        Index("ix_last_billing_time", "last_billing_time"),
        {
            "comment": "计费任务表"
        }
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # 资源信息
    resource_type = Column(
        Enum(ResourceType),
        nullable=False,
        comment="资源类型"
    )
    resource_id = Column(
        BigInteger,
        nullable=False,
        comment="资源ID，对应各资源表主键"
    )

    # 计费规则
    billing_method = Column(
        Enum(BillingMethod),
        nullable=False,
        comment="计费方式：PostPaid / PrePaid"
    )
    billing_cycle = Column(
        Enum(BillingCycle),
        nullable=False,
        comment="计费周期：HOUR / MONTH"
    )
    billing_period_count = Column(
        Integer,
        default=1,
        comment="计费周期数量"
    )

    unit_price = Column(
        DECIMAL(10, 4),
        nullable=False,
        comment="单价（元/小时 或 元/月）"
    )


    # 计费时间游标（核心）
    billing_start_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始计费时间"
    )
    last_billing_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="上一次成功结算到的时间"
    )
    next_bill_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="下次扣费时间"
    )

    # 仅 PREPAID 使用
    billing_end_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="计费结束时间（仅 PREPAID）"
    )
    auto_renew = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否自动续费（仅 PREPAID）"
    )

    status = Column(
        Enum(BillingStatus),
        nullable=False,
        default=BillingStatus.CREATED,
        comment="计费状态"
    )

    # 冗余字段
    cloud_provider_code = Column(String(50), nullable=False, comment="云厂商")
    region_id=Column(String(50), nullable=False, comment="区域")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")


    def __repr__(self):
        return (
            f"<BillingInstance(id={self.id}, "
            f"resource={self.resource_type.value}:{self.resource_id},"
            f" " f"method={self.billing_method.value},"
            f" " f"status={self.status.value})>"
        )