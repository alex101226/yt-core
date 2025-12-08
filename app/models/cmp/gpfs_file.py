# 状态， 存储类型，存储容量，已使用容量，计费方式，资源组，云厂商，区域，可用区，VPC，IP子网，价格，创建人，操作

from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, DECIMAL
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

"""
GPFS 文件存储实例表
"""
class GPFSFile(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}gpfs_file"
    __table_args__ = {'comment': 'GPFS 文件存储实例表'}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    # 基础信息
    fs_id = Column(String(128), unique=True, nullable=True, comment="云厂商返回的实例ID")
    fs_name = Column(String(128), nullable=False, comment="系统生成的实例名称")
    fs_alias = Column(String(128), nullable=True, comment="用户设置的别名")
    description = Column(String(512), nullable=True, comment="描述信息，可选")
    status = Column(String(32), nullable=False, comment="实例状态：字典表=FS_STATUS")

    # 配置信息
    storage_type = Column(String(64), nullable=False, comment="存储类型：SSD / HDD / 高性能型等")
    capacity_gb = Column(Integer, nullable=False, comment="配置的总容量（GB）")
    used_capacity_gb = Column(Integer, default=0, comment="已使用容量（GB）")

    performance_level = Column(String(64), nullable=True, comment="性能等级：standard / enhanced / high")
    iops = Column(Integer, nullable=True, comment="预设 IOPS（如云厂商支持）")
    throughput = Column(Integer, nullable=True, comment="吞吐量限制 MB/s（如云厂商支持）")

    # 网络 & 挂载信息
    protocol = Column(String(32), nullable=True, comment="协议：nfs / smb / posix / mixed")
    mount_targets = Column(JSON, nullable=True, comment="挂载目标数组：[{ip:..., port:...}]")
    mount_cmd = Column(String(512), nullable=True, comment="挂载命令（给用户展示）")

    vpc_id = Column(String(128), nullable=True, comment="VPC 网络ID")
    subnet_id = Column(String(128), nullable=True, comment="子网ID")
    network_access_group = Column(String(128), nullable=True, comment="网络访问组 / 挂载访问组")

    # 计费相关
    charge_type = Column(String(32), nullable=False, comment="计费方式：PrePaid / PostPaid")
    price = Column(DECIMAL(10, 2), nullable=True, comment="价格（展示用，实时价格另算）")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="到期时间（包年包月）")

    # 归属信息
    cloud_provider_code = Column(String(32), nullable=False, comment="云厂商：aliyun/aws/tencent/huawei/self")
    region_id = Column(String(64), nullable=False, comment="地域ID")
    zone_id = Column(String(64), nullable=True, comment="可用区ID")
    resource_group_id = Column(Integer, nullable=True, comment="资源组ID")
    created_by = Column(Integer, nullable=True, comment="创建人（用户ID）")

    # GPFS 特性
    fs_version = Column(String(64), nullable=True, comment="GPFS 文件系统版本")
    data_redundancy = Column(Integer, nullable=True, comment="数据副本数：2/3")
    block_size = Column(Integer, nullable=True, comment="块大小（KB）")

    # 时间
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
