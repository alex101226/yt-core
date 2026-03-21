from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.cmp.voucher_repo import VoucherRepository
from app.repositories.cmp.member_repo import MemberRepository
from app.schemas.cmp.voucher_schema import (
    VoucherTemplateCreateSchema,
    VoucherTemplatePageSchema,
    VoucherTemplateOutSchema,
    VoucherAssignCreateSchema,
    VoucherAssignPageSchema,
    VoucherAssignOutSchema,
)


class VoucherService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = VoucherRepository(db)
        self.member_repo = MemberRepository(db)

    def template_create(self, data: VoucherTemplateCreateSchema, operator: dict):
        payload = {
            **data.model_dump(),
            "template_no": f"VT-{generate(size=14)}",
            "created_by": operator.get("user_id"),
            "created_by_name": operator.get("username"),
        }
        try:
            self.repo.template_create(payload)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def template_page_list(
        self,
        page: int,
        page_size: int,
        cloud_provider_code: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
    ):
        items, total = self.repo.template_page_list(page, page_size, cloud_provider_code, amount_min, amount_max)
        now = datetime.utcnow()
        stats = self.repo.assign_stats_by_template([i.id for i in items])
        return VoucherTemplatePageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[
                VoucherTemplateOutSchema.model_validate({
                    **i.__dict__,
                    "is_expired": (
                        True if i.id not in stats
                        else (stats[i.id]["max_end"] is not None and stats[i.id]["max_end"] < now)
                    )
                }) for i in items
            ],
        )

    def template_delete(self, template_id: int):
        template = self.repo.template_get(template_id)
        if not template:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        # 仅允许删除：无分配记录，或所有分配已过期
        now = datetime.utcnow()
        stats = self.repo.assign_stats_by_template([template.id])
        if template.id in stats:
            max_end = stats[template.id]["max_end"]
            if max_end and max_end >= now:
                raise BusinessException(code=ErrorCode.FAILED, message="仅允许删除已过期模板")
        try:
            self.repo.template_delete(template)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def assign(self, data: VoucherAssignCreateSchema, operator: dict):
        template = self.repo.template_get(data.template_id)
        if not template:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="模板不存在")

        now = datetime.utcnow()
        # 会员校验
        for member_id in data.member_ids:
            member = self.member_repo.get_by_id(member_id)
            if not member:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="会员不存在")
            if self.repo.has_active_assign(data.template_id, member_id, now):
                raise BusinessException(code=ErrorCode.FAILED, message="会员已有未过期代金券，不能重复分配")

        payloads = []
        for member_id in data.member_ids:
            total_amount = (
                Decimal(str(template.amount)) * Decimal(str(data.quantity))
            ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
            payloads.append({
                "template_id": data.template_id,
                "member_id": member_id,
                "valid_start": data.valid_start,
                "valid_end": data.valid_end,
                "quantity": data.quantity,
                "remaining_amount": total_amount,
                "description": data.description,
                "created_by": operator.get("user_id"),
                "created_by_name": operator.get("username"),
            })

        try:
            self.repo.assign_create_many(payloads)
            self.db.commit()
            return True
        except Exception:
            self.db.rollback()
            raise

    def assign_page_list(self, page: int, page_size: int):
        items, total = self.repo.assign_page_list(page, page_size)
        return VoucherAssignPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[
                VoucherAssignOutSchema.model_validate({
                    **i._asdict(),
                    "consumed_amount": float((i.total_amount or 0) - (i.remaining_amount or 0)),
                })
                for i in items
            ],
        )

    def consume(
        self,
        member_id: int,
        cloud_provider_code: str,
        amount: float,
    ) -> float:
        if amount <= 0:
            return 0.0

        member = self.member_repo.get_active_by_id(member_id)
        if not member:
            return 0.0

        now = datetime.utcnow()
        assigns = self.repo.active_assigns_for_member(member_id, cloud_provider_code, now)
        remaining = Decimal(str(amount)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
        consumed = Decimal("0.00")

        try:
            for assign, _template_amount in assigns:
                if remaining <= 0:
                    break
                assign_remaining = Decimal(str(assign.remaining_amount or 0)).quantize(
                    Decimal("0.00"), rounding=ROUND_HALF_UP
                )
                if assign_remaining <= 0:
                    continue
                use_amount = min(assign_remaining, remaining)
                assign.remaining_amount = (assign_remaining - use_amount).quantize(
                    Decimal("0.00"), rounding=ROUND_HALF_UP
                )
                remaining = (remaining - use_amount).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                consumed += use_amount

            self.db.flush()
            return float(consumed)
        except Exception:
            self.db.rollback()
            raise
