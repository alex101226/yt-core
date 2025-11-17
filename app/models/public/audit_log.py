from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime
from app.core.config import settings
from app.core.database import PublicBase

class AuditLog(PublicBase):
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}audit_log"
    __table_args__ = {'comment': '操作审计日志表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(50), nullable=True, comment="操作用户ID")
    username = Column(String(100), nullable=True, comment="操作用户名")
    module = Column(String(100), nullable=False, comment="操作模块，例如 cloud、asset、user")
    action = Column(String(100), nullable=False, comment="操作动作，例如 create、update、delete")
    target_type = Column(String(100), nullable=True, comment="目标类型，例如 cloud_region、instance")
    target_id = Column(String(100), nullable=True, comment="目标对象ID")
    request_data = Column(Text, nullable=True, comment="操作请求参数（JSON）")
    description = Column(Text, nullable=True, comment="操作描述，例如 '创建云实例'")
    status = Column(String(20), nullable=False, default="success", comment="操作状态：success / failed")
    error_message = Column(Text, nullable=True, comment="失败时的错误信息")
    ip_address = Column(String(50), nullable=True, comment="请求来源IP")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)"
    )
