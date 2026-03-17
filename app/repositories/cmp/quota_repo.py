from typing import Optional

from sqlalchemy.orm import Session

from app.models.cmp.member import Member
from app.models.cmp.member_quota import MemberQuota
from app.models.cmp.quota_apply import QuotaApply
from app.models.cmp.quota_category import QuotaCategory


class QuotaRepository:
    def __init__(self, db: Session):
        self.db = db

    def category_list(self):
        return self.db.query(QuotaCategory).filter(QuotaCategory.is_released == 0).order_by(QuotaCategory.id.asc()).all()

    def get_category_by_id(self, category_id: int):
        return self.db.query(QuotaCategory).filter(
            QuotaCategory.id == category_id,
            QuotaCategory.is_released == 0,
        ).first()

    def get_category_by_code(self, quota_code: str):
        return self.db.query(QuotaCategory).filter(
            QuotaCategory.quota_code == quota_code,
            QuotaCategory.is_released == 0,
        ).first()

    def save_category(self, category: QuotaCategory):
        self.db.add(category)
        self.db.flush()
        return category

    def get_member_quota(self, member_id: int, cloud_provider_code: str, quota_code: str):
        return self.db.query(MemberQuota).filter(
            MemberQuota.member_id == member_id,
            MemberQuota.cloud_provider_code == cloud_provider_code,
            MemberQuota.quota_code == quota_code,
            MemberQuota.is_released == 0,
        ).first()

    def save_member_quota(self, member_quota: MemberQuota):
        self.db.add(member_quota)
        self.db.flush()
        return member_quota

    def create_apply(self, payload: dict):
        obj = QuotaApply(**payload)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_apply(self, apply_id: int):
        return self.db.query(QuotaApply).filter(
            QuotaApply.id == apply_id,
            QuotaApply.is_released == 0,
        ).first()

    def apply_page_list(
        self,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        quantity_type: Optional[str] = None,
        enabled: Optional[bool] = None,
        approve_status: Optional[str] = None,
    ):
        query = (
            self.db.query(
                QuotaApply.id,
                QuotaApply.member_id,
                Member.member_name,
                QuotaApply.cloud_provider_code,
                QuotaApply.quantity_type,
                QuotaApply.quota_name,
                QuotaApply.quota_code,
                QuotaApply.allocated_quota,
                QuotaApply.apply_quota,
                QuotaApply.apply_remark,
                QuotaApply.created_by_name,
                QuotaApply.approve_status,
                QuotaApply.approved_by_name,
                QuotaApply.approve_remark,
                QuotaApply.approved_at,
                QuotaApply.created_at,
            )
            .join(Member, Member.id == QuotaApply.member_id)
            .join(QuotaCategory, QuotaCategory.quota_code == QuotaApply.quota_code)
            .filter(QuotaApply.is_released == 0)
            .order_by(QuotaApply.id.desc())
        )
        if cloud_provider_code:
            query = query.filter(QuotaApply.cloud_provider_code == cloud_provider_code)
        if quantity_type:
            query = query.filter(QuotaApply.quantity_type == quantity_type)
        if enabled is not None:
            query = query.filter(QuotaCategory.enabled == enabled)
        if approve_status:
            query = query.filter(QuotaApply.approve_status == approve_status)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
