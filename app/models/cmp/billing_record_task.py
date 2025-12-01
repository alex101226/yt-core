# app/models/cmp/billing_record_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime, timezone
from app.core.database import CmpBase
from app.core.config import settings


class BillingRecordTask(CmpBase):
    """
    计费任务
    用于记录实例创建过程中产生的价格计算、扣费流程
    """
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}billing_task"
    __table_args__ = {"comment": "计费任务表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    main_task_id = Column(Integer, nullable=False, comment="关联主创建任务 ID")

    billing_method = Column(String(50), nullable=False, comment="计费方式：PostPaid（按量） / PrePaid（包年包月）")
    price_detail = Column(JSON, nullable=True, comment="价格明细快照")

    status = Column(
        Integer,
        nullable=False,
        default=1,
        comment="任务状态：1待执行(PENDING) 2执行中(RUNNING) 3成功(SUCCESS) 4失败(FAILED)"
    )
    error_message = Column(Text, nullable=True, comment="错误原因")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间（UTC）")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间（UTC）")
