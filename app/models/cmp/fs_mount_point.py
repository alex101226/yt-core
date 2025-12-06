from sqlalchemy import Column, String, Integer, Float, Boolean, JSON, DateTime
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings
from .is_released_mixin import IsReleasedMixin

class FileSystemMount(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}fs_mount_point"
    __table_args__ = {'comment': '文件系统挂载点'}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")

    # 关联
    fs_id = Column(Integer, nullable=False, comment="文件系统ID（CEPHFS/GPFS）")

    cloud_provider_code = Column(String(30), nullable=False, comment="云厂商code")
    region_id = Column(String(100), nullable=False, comment="区域ID")
    zone_id = Column(String(50), nullable=True, comment="可用区ID")

    instance_id = Column(Integer, nullable=False, comment="挂载到的服务器实例ID")
    vpc_id = Column(Integer, nullable=False, comment="挂载的vpc")
    subnet_id = Column(Integer, nullable=False, comment="挂载的子网")

    # 挂载属性
    mount_path = Column(String(256), nullable=False, comment="服务器内部的挂载路径，如 /mnt/cephfs01")
    mount_protocol = Column(String(32), nullable=False, comment="挂载协议，如 cephfs / nfs / posix")
    read_only = Column(Boolean, default=False, comment="是否只读挂载")

    # 状态
    status = Column(
        String(32), nullable=False, default="MOUNTING",
        comment="挂载状态：MOUNTING / MOUNTED / UNMOUNTING / ERROR"
    )

    # 审计
    created_by = Column(Integer, nullable=False, comment="创建人")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间(UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间(UTC)"
    )
