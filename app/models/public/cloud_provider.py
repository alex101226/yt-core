from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.core.config import settings
from app.core.database import PublicBase

class CloudCredentialsPlatform(PublicBase):
    # __tablename__ = "cloud_credentials_platform"
    __tablename__ = f"{settings.PUBLIC_TABLE_PREFIX}cloud_credentials_platform"
    __table_args__ = {'comment': '云厂商凭证与接入配置表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    provider_code = Column(String(50), nullable=False, unique=True, comment="云厂商编码，例如 aliyun")
    provider_name = Column(String(100), nullable=False, comment="云厂商名称")
    access_key_id = Column(String(200), nullable=False, comment="AccessKey ID")
    access_key_secret = Column(String(200), nullable=False, comment="AccessKey Secret（加密存储）")
    endpoint = Column(String(200), nullable=False, comment="默认 Endpoint，例如 ecs.aliyuncs.com")
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
