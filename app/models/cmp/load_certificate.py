# 协议证书

from datetime import datetime, timezone
from typing import Optional, Text

from sqlalchemy import Integer, String, Enum as SAEnum, DateTime, JSON, TEXT
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin

from ...constants.enums import LoadCertificateStatus


class LoadBalancerCertificate(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}load_certificate"
    __table_args__ = {'comment': '负载均衡证书'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    cert_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="云厂商证书ID")

    cert_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="证书名称")
    cert_domain: Mapped[str] = mapped_column(String(255), nullable=True, comment="证书主域名")
    expire_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True, comment="证书过期时间")

    status: Mapped[LoadCertificateStatus] = mapped_column(
        SAEnum(LoadCertificateStatus), nullable=False, comment="证书状态"
    )

    # 归属信息
    resource_group_id: Mapped[int] = mapped_column(
        Integer, nullable=True, comment="资源组ID"
    )
    cloud_provider_code: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="云厂商编码"
    )
    region_id: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="区域ID"
    )

    cert_content: Mapped[Text] = mapped_column(
        TEXT,
        nullable=False,
        comment="证书内容"
    )
    cert_key: Mapped[Text] = mapped_column(
        TEXT,
        nullable=False,
        comment="证书密钥"
    )

    # 元数据
    tags: Mapped[JSON] = mapped_column(JSON, nullable=True, comment="标签")
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="描述信息")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间"
    )
