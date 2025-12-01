# app/models/cmp/instance_provision_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

"""
ECS 创建子任务
记录阿里云 ECS 创建实例的异步任务过程
"""
class InstanceProvisionTask(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}instance_provision_task"
    __table_args__ = {"comment": "云服务器创建流程的子任务记录（虚拟机）"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    main_task_id = Column(Integer, nullable=False, comment="关联主创建任务 ID")

    ali_task_id = Column(String(100), nullable=True, comment="阿里云返回的异步任务 ID")
    instance_id = Column(String(100), nullable=True, comment="最终创建成功的实例 ID")

    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="任务状态：1待执行(PENDING) 2执行中(RUNNING) 3成功(SUCCESS) 4失败(FAILED)"
    )
    error_message = Column(Text, nullable=True, comment="错误原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
