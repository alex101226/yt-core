# models/account.py
from sqlalchemy import Column, BigInteger, Numeric, DateTime, Enum, String
from datetime import datetime, timezone
from app.core.config import settings
from app.core.database import CmpBase
from app.constants.enums import AccountType, AccountStatus
from app.models.is_released_mixin import IsReleasedMixin

class Account(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}account"
    __table_args__ = {"comment": "用户现金账户表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    account_name = Column(String(64), nullable=True, comment="账户名称")
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.PERSONAL, comment="账户类型")
    account_status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.ACTIVE, comment="账户状态")

    balance = Column(Numeric(18, 2), nullable=False, default=0, comment="可用余额")
    frozen_balance = Column(Numeric(18, 2), nullable=False, default=0, comment="冻结余额")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        comment="创建时间（UTC）"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间（UTC）"
    )