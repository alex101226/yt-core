from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, Enum, Boolean

from app.core.config import settings
from app.core.database import CmpBase
from .is_released_mixin import IsReleasedMixin

from app.constants.enums import ActionMode, ActionOperate

class AuditLog(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}audit_log"
    __table_args__ = {'comment': '操作审计日志表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 操作用户信息
    operate_id = Column(String(50), nullable=True, comment="操作用户ID")
    operate_name = Column(String(100), nullable=True, comment="操作用户名")

    # 系统信息，比如算力调度，资源纳管
    system =  Column(Integer, nullable=False, comment="系统类型:1:算力调度")
    system_name = Column(String(100), nullable=False, comment="系统名称")

    # 操作的模块
    action_mode = Column(
        Enum(ActionMode),
        nullable=False,
        comment="操作模块，例如SERVER=云服务器，DISK=cbs磁盘，EIP=公网eip，BAREMETAL=裸金属，CLUSTER=集群，"
                "CUSTOM_IMAGE=自定义镜像，LOAD_INSTANCE=负载均衡，GPFS=GPFS存储，OSS=oss存储，CEPHFS=CEPHFS存储，"
                "CONTAINER_IMAGE=容器镜像")

    # 操作动作
    action = Column(Enum(ActionOperate), nullable=False, comment="操作动作，例如 create、update、delete")

    # 操作数据id
    source_id = Column(String(100), nullable=True, comment="来源ID")

    # 这个是通知数据状态？
    status = Column(
        String(20),
        nullable=False,
        default="success",
        comment="状态：success / failed / warning / info"
    )

    # 通知的描述，比如某某创建成功，某某创建失败
    message = Column(Text, nullable=True, comment="操作描述，例如 '创建云实例'")

    ip_address = Column(String(50), nullable=True, comment="请求来源IP")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)"
    )
    # 已读，已读时间
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime(timezone=True), nullable=True, comment="阅读时间")
