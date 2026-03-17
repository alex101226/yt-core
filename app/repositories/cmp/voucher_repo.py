from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.cmp.voucher_template import VoucherTemplate
from app.models.cmp.voucher_assign import VoucherAssign
from app.models.cmp.member import Member
from sqlalchemy import func


class VoucherRepository:
    def __init__(self, db: Session):
        self.db = db

    def template_create(self, payload: dict) -> VoucherTemplate:
        obj = VoucherTemplate(**payload)
        self.db.add(obj)
        self.db.flush()
        return obj

    def template_page_list(
        self,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
    ) -> Tuple[List[VoucherTemplate], int]:
        query = self.db.query(VoucherTemplate).filter(VoucherTemplate.is_released == 0).order_by(VoucherTemplate.id.desc())
        if cloud_provider_code:
            query = query.filter(VoucherTemplate.cloud_provider_code == cloud_provider_code)
        if amount_min is not None:
            query = query.filter(VoucherTemplate.amount >= amount_min)
        if amount_max is not None:
            query = query.filter(VoucherTemplate.amount <= amount_max)
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def template_get(self, template_id: int):
        return self.db.query(VoucherTemplate).filter(VoucherTemplate.id == template_id, VoucherTemplate.is_released == 0).first()

    def template_delete(self, template: VoucherTemplate):
        template.is_released = True
        self.db.flush()
        return True

    def assign_create_many(self, payloads: List[dict]):
        objs = [VoucherAssign(**p) for p in payloads]
        self.db.add_all(objs)
        self.db.flush()
        return objs

    def has_active_assign(self, template_id: int, member_id: int, now):
        return self.db.query(VoucherAssign.id).filter(
            VoucherAssign.template_id == template_id,
            VoucherAssign.member_id == member_id,
            VoucherAssign.is_released == 0,
            VoucherAssign.valid_end >= now,
        ).first() is not None

    def assign_stats_by_template(self, template_ids: List[int]):
        if not template_ids:
            return {}
        rows = (
            self.db.query(
                VoucherAssign.template_id,
                func.count(VoucherAssign.id).label("cnt"),
                func.max(VoucherAssign.valid_end).label("max_end"),
            )
            .filter(VoucherAssign.is_released == 0, VoucherAssign.template_id.in_(template_ids))
            .group_by(VoucherAssign.template_id)
            .all()
        )
        return {r.template_id: {"count": r.cnt, "max_end": r.max_end} for r in rows}

    def assign_page_list(self, page: int, page_size: int):
        query = (
            self.db.query(
                VoucherAssign.id.label("assign_id"),
                VoucherAssign.member_id,
                Member.member_name,
                VoucherTemplate.cloud_provider_code,
                VoucherTemplate.amount,
                VoucherAssign.description,
                VoucherAssign.created_at,
            )
            .join(Member, Member.id == VoucherAssign.member_id)
            .join(VoucherTemplate, VoucherTemplate.id == VoucherAssign.template_id)
            .filter(VoucherAssign.is_released == 0)
            .order_by(VoucherAssign.id.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
