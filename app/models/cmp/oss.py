from sqlalchemy import Column, String, Integer, Boolean, JSON, DateTime
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin


class OssBucket(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}oss_bucket"
    __table_args__ = {'comment': 'OSS 存储桶资源表'}

    id = Column(Integer, primary_key=True, index=True)

    # 基础信息
    # 云端真实 bucket 名称（全局唯一）
    bucket_id = Column(String(128), unique=True, index=True, nullable=False, comment="云端真实 Bucket 名称（全局唯一）")
    bucket_name = Column(
        String(128), nullable=False,
        comment="展示名称（CMP 内部展示用）"
    )

    description = Column(
        String(512), nullable=True,
        comment="描述/备注"
    )
    tags = Column(
        JSON, nullable=True,
        comment="标签（key-value JSON）"
    )

    # 属性
    storage_class = Column(
        String(64), nullable=False,
        comment="存储类型：standard / infrequent / archive / cold_archive"
    )
    permission = Column(
        String(32), nullable=False,
        comment="访问权限：private-read-write / public-read-write / public-read-private-write"
    )
    endpoint = Column(
        String(256), nullable=False,
        comment="API Endpoint，例如 oss-cn-shanghai.aliyuncs.com"
    )

    public_url = Column(
        String(256), nullable=True,
        comment="公网访问域名"
    )

    accelerated = Column(
        Boolean, default=False,
        comment="是否开启加速"
    )

    versioning_enabled = Column(
        Boolean, default=False,
        comment="是否启用版本控制"
    )

    encryption_enabled = Column(
        Boolean, default=False,
        comment="是否开启服务端加密（SSE）"
    )

    # 文件统计
    object_count = Column(
        Integer, default=0,
        comment="对象数量（文件数量）"
    )

    used_size_bytes = Column(
        Integer, default=0,
        comment="已用空间（字节）"
    )

    # 计费
    charge_type = Column(
        String(32), nullable=False,
        comment="计费方式：PrePaid（包年包月）/ PostPaid（按量付费）"
    )

    billing_mode = Column(
        String(32), nullable=True,
        comment="计费模式，例如按存储量/请求量"
    )

    # 生命周期/审计
    lifecycle_rules = Column(
        JSON, nullable=True,
        comment="生命周期规则（JSON）"
    )

    access_log_enabled = Column(
        Boolean, default=False,
        comment="是否开启访问日志"
    )

    # 跨区域复制
    replication_enabled = Column(
        Boolean, default=False,
        comment="是否开启跨区域复制（CRR）"
    )

    replication_region = Column(
        String(64), nullable=True,
        comment="跨区域复制目标区域"
    )

    # 云相关
    cloud_provider_code = Column(
        String(32), nullable=False,
        comment="云厂商：aliyun / aws / tencent / huawei 等"
    )

    region_id = Column(
        String(64), nullable=False,
        comment="区域 ID，例如：cn-shanghai"
    )

    resource_group_id = Column(
        Integer, nullable=True,
        comment="CMP 资源组 ID"
    )

    user_id = Column(
        Integer, nullable=False,
        comment="创建人（用户 ID）"
    )

    status = Column(
        String(32), default="CREATING",
        comment="状态：CREATING/ACTIVE/UPDATING/DELETING/ERROR"
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )

