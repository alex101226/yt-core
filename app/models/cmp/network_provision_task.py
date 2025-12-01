# app/models/cmp/network_provision_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings


class NetworkProvisionTask(CmpBase):
    """
    网络资源创建任务
    记录 VPC / 交换机 / 安全组 等网络资源的创建状态
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}network_task"
    __table_args__ = {"comment": "网络创建任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    main_task_id = Column(Integer, nullable=False, comment="关联主创建任务 ID")

    resource_type = Column(String(50), nullable=False, comment="资源类型：VPC / VSWITCH / SECURITY_GROUP")
    resource_id = Column(String(100), nullable=True, comment="创建成功后的资源 ID")

    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="任务状态：1待执行(PENDING) 2执行中(RUNNING) 3成功(SUCCESS) 4失败(FAILED)"
    )
    error_message = Column(Text, nullable=True, comment="错误原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
