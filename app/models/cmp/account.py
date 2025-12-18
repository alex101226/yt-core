# models/account.py
from sqlalchemy import Column, BigInteger, Numeric, DateTime, ForeignKey, Integer
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from app.core.config import settings
from app.core.database import CmpBase


class Account(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}account"
    __table_args__ = {"comment": "用户现金账户表"}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, nullable=False, unique=True, comment="关联用户ID")

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