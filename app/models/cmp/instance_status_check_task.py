# app/models/cmp/instance_status_check_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings


class InstanceStatusCheckTask(CmpBase):
    """
    实例状态检查任务
    用于轮询阿里云实例状态，直到 Running
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}instance_status_check_task"
    __table_args__ = {"comment": "实例状态检查任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    main_task_id = Column(Integer, nullable=False, comment="关联主创建任务 ID")

    instance_id = Column(String(100), nullable=False, comment="云实例 ID")
    check_count = Column(Integer, nullable=False, default=0, comment="检查次数")
    max_check = Column(Integer, nullable=False, default=30, comment="最大允许检查次数")

    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="任务状态：1待执行(PENDING) 2执行中(RUNNING) 3成功(SUCCESS) 4失败(FAILED)"
    )
    error_message = Column(Text, nullable=True, comment="失败原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
