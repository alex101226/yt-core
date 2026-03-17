from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.core.database import CmpBase
from app.core.config import settings
from app.models.is_released_mixin import IsReleasedMixin


class Member(CmpBase, IsReleasedMixin):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}members"
    __table_args__ = {"comment": "会员表"}

    id = Column(Integer, primary_key=True, comment="会员ID")
    user_id = Column(Integer, nullable=True, unique=True, comment="用户ID(一对一)")

    member_name = Column(String(128), nullable=False, comment="会员名称/企业名称")
    member_type = Column(String(20), nullable=False, comment="会员类型：PERSONAL/COMPANY")
    credit_code = Column(String(64), nullable=True, comment="社会信用码(企业)")
    contact_phone = Column(String(32), nullable=True, comment="联系电话")
    contact_email = Column(String(128), nullable=True, comment="邮箱")
    industry = Column(String(64), nullable=True, comment="行业分类")
    address = Column(String(255), nullable=True, comment="地址")
    description = Column(String(255), nullable=True, comment="描述/备注")

    member_person_name = Column(String(64), nullable=True, comment="会员姓名")
    member_account = Column(String(64), nullable=True, comment="会员账号(用户账号)")

    is_frozen = Column(Boolean, default=False, nullable=False, comment="是否冻结")

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="创建时间(UTC)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="更新时间(UTC)"
    )
