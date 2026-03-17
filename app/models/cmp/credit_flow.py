from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin


class CreditFlow(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}credit_flow"
    __table_args__ = {"comment": "低佣金流水表"}

    id = Column(Integer, primary_key=True, autoincrement=True, comment="流水ID")
    grant_id = Column(Integer, nullable=True, comment="发放记录ID")
    member_id = Column(Integer, nullable=False, comment="会员ID")
    amount = Column(Numeric(18, 2), nullable=False, comment="金额")
    direction = Column(String(8), nullable=False, comment="方向：IN/OUT")
    flow_type = Column(String(32), nullable=False, comment="类型：GRANT/CONSUME/EXPIRE/ADJUST")
    cloud_provider_code = Column(String(32), nullable=True, comment="云厂商编码")
    ref_type = Column(String(32), nullable=True, comment="关联类型")
    ref_id = Column(String(64), nullable=True, comment="关联ID")
    description = Column(String(255), nullable=True, comment="描述/备注")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间(UTC)"
    )
