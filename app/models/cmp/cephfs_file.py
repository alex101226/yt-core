from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

class CephfsFile(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}cephfs_file"
    __table_args__ = {'comment': 'CEPHFS 文件系统表'}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    # -------------------------------
    # 基础信息
    # -------------------------------
    fs_id = Column(String(128), unique=True, nullable=False, comment="文件系统唯一 ID")
    fs_name = Column(String(128), nullable=False, comment="文件系统名称（展示用）")
    description = Column(String(512), nullable=True, comment="描述信息，可选")

    # -------------------------------
    # 云平台相关
    # -------------------------------
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商：aliyun / aws / tencent / huawei 等")
    region_id = Column(String(64), nullable=False, comment="区域 ID，例如 cn-shanghai")
    # zone_id = Column(String(64), nullable=True, comment="可用区 ID，可选")
    resource_group_id = Column(Integer, nullable=True, comment="资源组 ID，可选")

    # -------------------------------
    # 存储与计费
    # -------------------------------
    charge_type = Column(String(32), nullable=False, comment="计费方式：PrePaid / PostPaid")
    storage_type = Column(String(64), nullable=False, comment="存储类型：普通 / 高性能 / 冷存储等")
    capacity_gb = Column(Integer, nullable=False, comment="分配容量（GB）")
    used_size_gb = Column(Integer, default=0, comment="已使用容量（GB）")
    price = Column(Float, nullable=True, comment="价格（可按月或按量计费）")

    # -------------------------------
    # 状态与操作
    # -------------------------------
    status = Column(String(32), default="CREATING", comment="文件系统状态：CREATING/ACTIVE/UPDATING/DELETING/ERROR")
    operations = Column(JSON, nullable=True, comment='可操作类型，例如 ["EXPAND_CAPACITY", "RELEASE"]')

    # -------------------------------
    # 快照信息（可选）
    # -------------------------------
    snapshot_count = Column(Integer, default=0, comment="快照数量")
    last_snapshot_time = Column(DateTime(timezone=True), nullable=True, comment="最近快照时间（UTC）")

    # -------------------------------
    # 审计信息
    # -------------------------------
    user_id = Column(Integer, nullable=False, comment="用户 ID")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）"
    )
