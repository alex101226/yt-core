from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Boolean
from app.core.config import settings
from app.core.database import CmpBase
from app.models.is_released_mixin import IsReleasedMixin

class Invoice(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}invoice"
    __table_args__ = {'comment': '发票信息表'}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 发票抬头信息
    invoice_title = Column(String(128), nullable=False, comment='发票抬头名称')
    title_type = Column(String(20), nullable=False, comment='抬头类型 personal/company')
    invoice_type = Column(String(20), nullable=False, comment='发票类型 normal/vat')

    # 企业信息（个人可为空）
    bank_name = Column(String(64), comment='开户银行名称')
    bank_account = Column(String(64), comment='基本开户账号')
    company_address = Column(String(255), comment='注册场所地址')
    company_phone = Column(String(32), comment='注册固定电话')
    taxpayer_id = Column(String(32), comment='统一社会信用代码')

    # 状态控制
    is_default = Column(Boolean, default=False, comment='是否默认抬头')
    status = Column(String(20), default='enabled', comment='状态 enabled/disabled')

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
        comment="更新时间（UTC）"
    )