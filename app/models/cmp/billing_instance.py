# app/models/cmp/billing_instance.py
import enum

from sqlalchemy import Column, DateTime, BigInteger, DECIMAL, Boolean, UniqueConstraint, Index, Enum, String
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

class ResourceType(enum.Enum):
    SERVER = "SERVER"   # 服务器
    DISK = "DISK"   # 磁盘
    EIP = "EIP" # eip公网
    BAREMETAL = "BAREMETAL" # 裸金属
    CLUSTER = "CLUSTER" # 集群
    CUSTOM_IMAGE = "CUSTOM_IMAGE"   # 自定义镜像
    LOAD_INSTANCE = "LOAD_INSTANCE" # 负载均衡
    GPFS = "GPFS"   # gpfs存储
    OSS = "OSS" # OSS存储
    CEPHFS = "CEPHFS" # cephfs存储
    CONTAINER_IMAGE = "CONTAINER_IMAGE"  # 容器镜像


class BillingMethod(enum.Enum):
    POSTPAID = "POSTPAID"   # 按量
    PREPAID = "PREPAID"     # 包年包月


class BillingCycle(enum.Enum):
    HOUR = "HOUR"
    MONTH = "MONTH"


class BillingStatus(enum.Enum):
    ACTIVE = "ACTIVE"        # 正常计费
    SUSPENDED = "SUSPENDED"  # 欠费/暂停
    RELEASED = "RELEASED"    # 已释放

class BillingInstance(CmpBase):
    """
    计费任务
    用于记录实例创建过程中产生的价格计算、扣费流程
    """
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
        comment="计费方式：POSTPAID / PREPAID"
    )
    billing_cycle = Column(
        Enum(BillingCycle),
        nullable=False,
        comment="计费周期：HOUR / MONTH"
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

    # 仅 PREPAID 使用
    billing_end_time = Column(
        DateTime,
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
        default=BillingStatus.ACTIVE,
        comment="计费状态"
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")


    def __repr__(self):
        return (
            f"<BillingInstance(id={self.id}, "
            f"resource={self.resource_type.value}:{self.resource_id},"
            f" " f"method={self.billing_method.value},"
            f" " f"status={self.status.value})>"
        )