# app/models/cmp/volume_create_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings

"""
数据盘创建任务
记录系统盘以外的所有磁盘创建情况
"""
class VolumeCreateTask(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}volume_create_task"
    __table_args__ = {"comment": "数据盘创建任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    main_task_id = Column(Integer, nullable=False, comment="关联主创建任务 ID")

    disk_category = Column(String(50), nullable=False, comment="数据盘类型：ESSD_PL0 / SSD / SATA")
    disk_size = Column(Integer, nullable=False, comment="数据盘大小（GB）")
    encrypted = Column(Boolean, nullable=False, default=False, comment = "是否加密")
    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="任务状态：1待执行(PENDING) 2执行中(RUNNING) 3成功(SUCCESS) 4失败(FAILED)"
    )
    error_message = Column(Text, nullable=True, comment="错误原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
