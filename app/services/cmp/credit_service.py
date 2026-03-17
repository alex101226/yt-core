from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.constants.enums import ActionMode, ActionOperate
from app.repositories.cmp.credit_repo import CreditRepository
from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.sso.user_repo import UserRepository
from app.schemas.cmp.state_schema import AuditLogSchema
from app.services.cmp.operation_helper import _write_audit_log
from app.schemas.cmp.credit_schema import (
    CreditBalanceItemSchema,
    CreditBalanceSchema,
    CreditFlowOutSchema,
    CreditFlowPageSchema,
    CreditGrantCreateSchema,
    CreditGrantOutSchema,
    CreditGrantPageSchema,
    CreditOverviewCardsSchema,
    CreditOverviewSchema,
    CreditOverviewSummarySchema,
    CreditTopMemberSchema,
    CreditTrendPointSchema,
)


class CreditService:
    def __init__(self, sso_db: Session, cmp_db: Session):
        self.sso_db = sso_db
        self.cmp_db = cmp_db
        self.repo = CreditRepository(cmp_db)
        self.user_repo = UserRepository(sso_db)
        self.member_repo = MemberRepository(cmp_db)

    def _write_credit_audit_log(
        self,
        *,
        operator: dict,
        action: str,
        source_id: str,
        message: str,
        status: str = "success",
    ):
        data = AuditLogSchema(
            created_by=operator.get("user_id", 0),
            created_by_name=operator.get("username"),
            system=2,
            system_name="运营工作台",
            action_mode=ActionMode.CREDIT.value,
            action=action,
            source_id=source_id,
            message=message,
            status=status,
        )
        _write_audit_log(data)

    def _get_internal_operator(self, operator: dict):
        operator_user = self.user_repo.get_by_id(operator.get("user_id"))
        if not operator_user or operator_user.user_type != "internal":
            raise BusinessException(code=ErrorCode.FAILED, message="仅内部人员可操作低佣金")
        return operator_user

    def _resolve_member_for_user(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        owner_user_id = user.id if user.parent_id == 0 else user.parent_id
        member = self.member_repo.get_by_user_id(owner_user_id)
        if not member or member.is_frozen:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前账号未绑定有效会员")
        return member

    def _resolve_target_member(self, current_user: dict, member_id: Optional[int] = None):
        operator_user = self.user_repo.get_by_id(current_user.get("user_id"))
        if operator_user and operator_user.user_type == "internal":
            if member_id:
                member = self.member_repo.get_by_id(member_id)
                if not member:
                    raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="会员不存在")
                return member
            raise BusinessException(code=ErrorCode.FAILED, message="member_id不能为空")
        return self._resolve_member_for_user(current_user.get("user_id"))

    def grant(self, data: CreditGrantCreateSchema, operator: dict):
        self._get_internal_operator(operator)
        member = self.member_repo.get_active_by_id(data.member_id)
        if not member:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="会员不存在或已冻结")

        if data.amount <= 0:
            raise BusinessException(code=ErrorCode.FAILED, message="金额必须大于0")
        if data.valid_end <= data.valid_start:
            raise BusinessException(code=ErrorCode.FAILED, message="结束时间必须大于开始时间")

        payload = {
            **data.model_dump(),
            "remaining_amount": Decimal(str(data.amount)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP),
            "status": "ACTIVE",
            "source_type": "INTERNAL",
            "approve_status": "PENDING",
            "created_by": operator.get("user_id"),
            "created_by_name": operator.get("username"),
        }

        try:
            grant = self.repo.create_grant(payload)
            self.repo.create_flow({
                "grant_id": grant.id,
                "member_id": data.member_id,
                "amount": payload["remaining_amount"],
                "direction": "IN",
                "flow_type": "GRANT",
                "cloud_provider_code": data.cloud_provider_code,
                "ref_type": "CREDIT_GRANT",
                "ref_id": str(grant.id),
                "description": data.description,
                "created_by": operator.get("user_id"),
                "created_by_name": operator.get("username"),
            })
            self.cmp_db.commit()
            self._write_credit_audit_log(
                operator=operator,
                action=ActionOperate.CREATE.value,
                source_id=str(grant.id),
                message=f"低佣金充值申请已提交，会员：{member.member_name}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def approve(self, grant_id: int, operator: dict):
        self._get_internal_operator(operator)
        grant = self.repo.get_grant(grant_id)
        if not grant:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if grant.approve_status == "APPROVED":
            raise BusinessException(code=ErrorCode.FAILED, message="该记录已审批通过")
        if grant.approve_status == "REJECTED":
            raise BusinessException(code=ErrorCode.FAILED, message="该记录已被驳回")

        grant.approve_status = "APPROVED"
        grant.approved_by = operator.get("user_id")
        grant.approved_by_name = operator.get("username")
        grant.approved_at = datetime.utcnow()
        try:
            self.cmp_db.commit()
            member = self.member_repo.get_by_id(grant.member_id)
            self._write_credit_audit_log(
                operator=operator,
                action=ActionOperate.APPROVE.value,
                source_id=str(grant.id),
                message=f"低佣金审批通过，会员：{member.member_name if member else grant.member_id}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def reject(self, grant_id: int, reason: Optional[str], operator: dict):
        self._get_internal_operator(operator)
        grant = self.repo.get_grant(grant_id)
        if not grant:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if grant.approve_status == "APPROVED":
            raise BusinessException(code=ErrorCode.FAILED, message="该记录已审批通过")
        if grant.approve_status == "REJECTED":
            raise BusinessException(code=ErrorCode.FAILED, message="该记录已被驳回")

        grant.approve_status = "REJECTED"
        grant.reject_reason = reason
        grant.approved_by = operator.get("user_id")
        grant.approved_by_name = operator.get("username")
        grant.approved_at = datetime.utcnow()
        try:
            self.cmp_db.commit()
            member = self.member_repo.get_by_id(grant.member_id)
            self._write_credit_audit_log(
                operator=operator,
                action=ActionOperate.REJECT.value,
                source_id=str(grant.id),
                message=f"低佣金审批驳回，会员：{member.member_name if member else grant.member_id}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def balance(self, current_user: dict, member_id: Optional[int] = None):
        member = self._resolve_target_member(current_user, member_id)
        now = datetime.utcnow()
        self.repo.expire_grants(member.id, now)
        self.cmp_db.commit()
        rows = self.repo.balance_by_cloud_provider(member.id, now)
        items = [
            CreditBalanceItemSchema(
                cloud_provider_code=row.cloud_provider_code,
                total_amount=float(row.total_amount or 0),
                distributed_amount=float(row.distributed_amount or 0),
                expired_amount=float(row.expired_amount or 0),
                remaining_amount=float(row.remaining_amount or 0),
            )
            for row in rows
        ]
        return CreditBalanceSchema(
            member_id=member.id,
            member_name=member.member_name,
            total_amount=sum(i.total_amount for i in items),
            distributed_amount=sum(i.distributed_amount for i in items),
            expired_amount=sum(i.expired_amount for i in items),
            remaining_amount=sum(i.remaining_amount for i in items),
            items=items,
        )

    def grant_page_list(
        self,
        current_user: dict,
        page: int,
        page_size: int,
        member_id: Optional[int] = None,
        cloud_provider_code: Optional[str] = None,
        status: Optional[str] = None,
        approve_status: Optional[str] = None,
    ):
        target_member_id = None
        operator_user = self.user_repo.get_by_id(current_user.get("user_id"))
        if operator_user and operator_user.user_type == "internal":
            target_member_id = member_id
        else:
            target_member_id = self._resolve_member_for_user(current_user.get("user_id")).id

        items, total = self.repo.grant_page_list(
            page, page_size, target_member_id, cloud_provider_code, status, approve_status
        )
        return CreditGrantPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[
                CreditGrantOutSchema.model_validate({
                    **item._asdict(),
                    "audit_result": item.approve_status,
                })
                for item in items
            ],
        )

    def flow_page_list(
        self,
        current_user: dict,
        page: int,
        page_size: int,
        member_id: Optional[int] = None,
    ):
        operator_user = self.user_repo.get_by_id(current_user.get("user_id"))
        if operator_user and operator_user.user_type == "internal":
            target_member_id = member_id
        else:
            target_member_id = self._resolve_member_for_user(current_user.get("user_id")).id

        items, total = self.repo.flow_page_list(page, page_size, target_member_id)
        return CreditFlowPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[CreditFlowOutSchema.model_validate(item._asdict()) for item in items],
        )

    def consume(
        self,
        user_id: int,
        cloud_provider_code: str,
        amount: float,
        ref_type: str,
        ref_id: str,
        description: str,
        operator: Optional[dict] = None,
    ) -> float:
        if amount <= 0:
            return 0.0

        member = self._resolve_member_for_user(user_id)
        now = datetime.utcnow()
        self.repo.expire_grants(member.id, now)
        grants = self.repo.active_grants_for_member(member.id, cloud_provider_code, now)
        remaining = Decimal(str(amount))
        consumed = Decimal("0.00")

        try:
            for grant in grants:
                if remaining <= 0:
                    break
                grant_remaining = Decimal(str(grant.remaining_amount))
                if grant_remaining <= 0:
                    continue
                use_amount = min(grant_remaining, remaining)
                grant.remaining_amount = (grant_remaining - use_amount).quantize(
                    Decimal("0.00"), rounding=ROUND_HALF_UP
                )
                if grant.remaining_amount == 0:
                    grant.status = "USED_UP"
                remaining = (remaining - use_amount).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                consumed += use_amount
                self.repo.create_flow({
                    "grant_id": grant.id,
                    "member_id": member.id,
                    "amount": use_amount,
                    "direction": "OUT",
                    "flow_type": "CONSUME",
                    "cloud_provider_code": cloud_provider_code,
                    "ref_type": ref_type,
                    "ref_id": ref_id,
                    "description": description,
                    "created_by": (operator or {}).get("user_id"),
                    "created_by_name": (operator or {}).get("username"),
                })

            self.cmp_db.commit()
            return float(consumed)
        except Exception:
            self.cmp_db.rollback()
            raise

    def overview(self, current_user: dict):
        operator_user = self.user_repo.get_by_id(current_user.get("user_id"))
        target_member_id = None
        if not operator_user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        if operator_user.user_type != "internal":
            target_member_id = self._resolve_member_for_user(current_user.get("user_id")).id

        now = datetime.utcnow()
        summary = self.repo.overview_summary(now, target_member_id)
        cards = self.repo.overview_cards(now, target_member_id)
        order_trend_map, order_start = self.repo.recent_order_trend(now, member_id=target_member_id)
        consume_trend_map, consume_start = self.repo.recent_consume_amount_trend(now, member_id=target_member_id)
        order_top = self.repo.today_order_top10_members(now, target_member_id)
        amount_top = self.repo.today_amount_top10_members(now, target_member_id)

        recent_order_trend = []
        recent_consume_amount_trend = []
        for idx in range(7):
            day = order_start + timedelta(days=idx)
            key = day.strftime("%m-%d")
            recent_order_trend.append(
                CreditTrendPointSchema(date=key, value=float(order_trend_map.get(key, 0)))
            )
            recent_consume_amount_trend.append(
                CreditTrendPointSchema(date=key, value=float(consume_trend_map.get(key, 0)))
            )

        return CreditOverviewSchema(
            summary=CreditOverviewSummarySchema(
                remaining_distributable_amount=float(summary.remaining_distributable_amount or 0),
                total_amount=float(summary.total_amount or 0),
                expired_amount=float(summary.expired_amount or 0),
                distributed_amount=float(summary.distributed_amount or 0),
                today_distributed_amount=float(summary.today_distributed_amount or 0),
            ),
            cards=CreditOverviewCardsSchema(
                today_new_order_count=int(cards["today_new_order_count"]),
                today_consume_amount=float(cards["today_consume_amount"]),
                today_distributed_member_count=int(cards["today_distributed_member_count"]),
                today_consume_member_count=int(cards["today_consume_member_count"]),
                total_order_count=int(cards["total_order_count"]),
                total_consume_amount=float(cards["total_consume_amount"]),
                total_distributed_member_count=int(cards["total_distributed_member_count"]),
                total_consume_member_count=int(cards["total_consume_member_count"]),
            ),
            recent_order_trend=recent_order_trend,
            recent_consume_amount_trend=recent_consume_amount_trend,
            today_order_top10_members=[
                CreditTopMemberSchema(
                    member_id=item.member_id,
                    member_name=item.member_name,
                    value=float(item.value or 0),
                )
                for item in order_top
            ],
            today_amount_top10_members=[
                CreditTopMemberSchema(
                    member_id=item.member_id,
                    member_name=item.member_name,
                    value=float(item.value or 0),
                )
                for item in amount_top
            ],
        )
