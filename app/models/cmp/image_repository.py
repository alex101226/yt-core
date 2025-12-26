from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum, DECIMAL, JSON, Float
from datetime import datetime, timezone

from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin


class ImageRepository(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}image_repository"
    __table_args__ = {'comment': '镜像仓库表'}


    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id= Column(String(50), unique=True, index=True, nullable=False, comment="创建后返回的仓库实例id")
    repository_name = Column(String(128), nullable=False, comment="仓库名称")
    description = Column(String(256), nullable=True, comment="仓库描述")
    namespace_count = Column(Integer, default=1, comment="命名空间数量")
    namespace_list = Column(JSON, default=list, comment="命名空间列表")

    # 实例规格
    instance_spec = Column(String(64), default="Basic", comment="实例规格")
    capacity_gb = Column(Integer, nullable=True, comment="配置的总容量（GB）")
    used_capacity_gb = Column(Integer, default=0, comment="已使用容量（GB）")

    # 实例存储
    cephfs_id = Column(Integer, nullable=False, comment="实例存储id")

    # 访问方式
    endpoint_type = Column(String(64), nullable=False, default="PUBLIC", comment="访问方式, 字典表item_code=ENDPOINT_TYPE")
    endpoint_url = Column(String(256), nullable=True, comment="访问地址")
    enable_public_access = Column(String(64), default="PUBLIC", comment="是否允许公网访问")
    enable_https = Column(Boolean, default=True, comment="是否强制 HTTPS")

    status = Column(String(64), default="AVAILABLE", comment="仓库状态，字典表item_code=REPOSITORY_STATUS")

    # 计费相关
    charge_type = Column(String(32), default="PrePaid", comment="计费方式：PrePaid / PostPaid")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="到期时间")
    price = Column(DECIMAL(18,2), nullable=True, comment="单价")

    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    region_id = Column(String(100), nullable=False, comment="区域ID")
    resource_group_id = Column(
        Integer,
        nullable=True,
        comment="资源组 ID"
    )
    created_by=Column(Integer, nullable=False, comment="提交用户ID")
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
