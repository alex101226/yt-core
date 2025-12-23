from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, JSON, Text

from app.core.config import settings
from app.core.database import CmpBase
from .is_released_mixin import IsReleasedMixin

class CbsDisk(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cbs_disks"
    __table_args__ = {"comment": "CBS 云盘资源表"}

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="自增主键"
    )
    user_id = Column(Integer, nullable=False, comment="提交用户ID")
    # 云盘基础身份
    disk_id = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="云厂商返回的云盘 ID"
    )

    disk_name = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="磁盘名称"
    )

    cloud_provider_code = Column(
        String(32),
        nullable=False,
        comment="云厂商标识，如 aliyun/tencent/huaweicloud"
    )
    region_id = Column(
        String(32),
        nullable=False,
        comment="地域 ID"
    )
    zone_id = Column(
        String(32),
        nullable=True,
        comment="可用区 ID"
    )
    resource_group_id = Column(
        Integer,
        nullable=True,
        comment="资源组 ID"
    )

    # 规格
    disk_type = Column(
        String(15),
        nullable=False,
        comment="磁盘类型：system 系统盘 / data 数据盘"
    )
    disk_category = Column(
        String(32),
        nullable=False,
        comment="磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等"
    )
    disk_size = Column(
        Integer,
        nullable=False,
        comment="磁盘大小（GB）"
    )

    iops_level = Column(
        String(32),
        nullable=True,
        comment="性能等级（IOPS 规格），如 ESSD PL0/1/2，不同云不同含义"
    )
    tags = Column(JSON, nullable=True, comment="标签")
    description = Column(Text, nullable=True, comment="描述，可选")

    # 加密
    encrypted = Column(
        Boolean,
        default=False,
        comment="是否加密：1 是 / 0 否"
    )
    encryption_key_id = Column(
        String(128),
        nullable=True,
        comment="加密使用的 KMS 密钥 ID"
    )

    # 计费
    price = Column(Float, nullable=True, comment="按量计费价格（元/小时）")
    charge_type = Column(
        String(15),
        nullable=False,
        comment="计费方式：PrePaid 包年包月 / PostPaid 按量付费"
    )
    period = Column(
        Integer,
        nullable=True,
        comment="购买时长（月），仅当 PrePaid 时有效"
    )
    auto_renew = Column(
        Boolean,
        default=False,
        comment="是否自动续费：1 是 / 0 否"
    )
    expired_time = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="云盘到期时间（UTC）"
    )

    # 状态
    status = Column(
        String(15),
        nullable=False,
        default="Creating",
        comment="云盘状态：字典表的CBS_STATUS"
    )

    # 挂载相关
    is_attached = Column(
        Boolean,
        default=False,
        comment="是否自动挂载"
    )
    attached_instance_id = Column(
        String(64),
        nullable=True,
        comment="挂载的实例 ID（ecs/lh/lb）"
    )
    attached_device = Column(
        String(64),
        nullable=True,
        comment="挂载点名称，如 /dev/vdb"
    )
    attached_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
        comment="挂载时间（UTC）"
    )
    detached_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
        comment="卸载时间（UTC）"
    )

    # 快照统计
    snapshot_count = Column(
        Integer,
        default=0,
        comment="已创建的快照数量"
    )
    last_snapshot_time = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=True,
        comment="最近一次创建快照的时间（UTC）"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="记录创建时间（UTC）"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="记录更新时间（UTC）"
    )
