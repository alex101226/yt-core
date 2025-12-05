# app/models/cmp/sync_resource_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings


class SyncResourceTask(CmpBase):
    """
    云资源同步任务
    用于在实例创建成功后，同步来自阿里云的最新信息（IP、状态、带宽等）
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}sync_resource_task"
    __table_args__ = {"comment": "云资源同步任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(String(100), nullable=False, comment="云实例 ID，创建成功后返回的")
    sync_type = Column(String(50), nullable=False, comment="同步类型：INSTANCE / DISK / NETWORK / BILLING")

    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        comment="任务状态：字典表type_code=TASK_STATUS"
    )
    error_message = Column(Text, nullable=True, comment="错误原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
