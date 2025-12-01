from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, func
from app.core.config import settings
from app.core.database import CmpBase

class UserCertificate(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}user_certificate"
    __table_args__ = {'comment': '用户云厂商的云凭证'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False, comment="属于哪个用户")
    cloud_code = Column(String(50), nullable=False, unique=True, comment="云凭证编码，例如 aliyun")
    cloud_name = Column(String(100), nullable=False, comment="云凭证名称")
    cloud_access_key_id = Column(String(200), nullable=False, comment="AccessKey ID")
    cloud_access_key_secret = Column(String(200), nullable=False, comment="AccessKey Secret（加密存储）")
    is_default = Column(Boolean, default=False)
    description = Column(Text, nullable=True, comment="描述信息")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间 (UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间 (UTC)"
    )
