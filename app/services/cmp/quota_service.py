from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.constants.enums import ActionMode, ActionOperate
from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.cmp.quota_repo import QuotaRepository
from app.repositories.sso.user_repo import UserRepository
from app.schemas.cmp.quota_schema import (
    QuotaApplyApproveSchema,
    QuotaApplyCreateSchema,
    QuotaApplyOutSchema,
    QuotaApplyPageSchema,
    QuotaApplyRejectSchema,
    QuotaCategoryOutSchema,
    QuotaCategoryToggleSchema,
)
from app.schemas.cmp.state_schema import AuditLogSchema
from app.services.cmp.operation_helper import _write_audit_log
from app.models.cmp.member_quota import MemberQuota


class QuotaService:
    def __init__(self, sso_db: Session, cmp_db: Session):
        self.sso_db = sso_db
        self.cmp_db = cmp_db
        self.repo = QuotaRepository(cmp_db)
        self.user_repo = UserRepository(sso_db)
        self.member_repo = MemberRepository(cmp_db)

    def _require_internal(self, operator: dict):
        user = self.user_repo.get_by_id(operator.get("user_id"))
        if not user or user.user_type != "internal":
            raise BusinessException(code=ErrorCode.FAILED, message="仅内部人员可操作配额管理")
        return user

    def _write_quota_audit_log(self, operator: dict, action: str, source_id: str, message: str):
        _write_audit_log(
            AuditLogSchema(
                created_by=operator.get("user_id", 0),
                created_by_name=operator.get("username"),
                system=2,
                system_name="运营工作台",
                action_mode=ActionMode.SYSTEM_CONFIG.value,
                action=action,
                source_id=source_id,
                message=message,
                status="success",
            )
        )

    def category_list(self):
        items = self.repo.category_list()
        return [QuotaCategoryOutSchema.model_validate(item) for item in items]

    def category_toggle(self, operator: dict, data: QuotaCategoryToggleSchema):
        self._require_internal(operator)
        category = self.repo.get_category_by_id(data.category_id)
        if not category:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        category.enabled = data.enabled
        try:
            self.repo.save_category(category)
            self.cmp_db.commit()
            self._write_quota_audit_log(
                operator,
                ActionOperate.UPDATE.value,
                str(category.id),
                f"配额类别{category.quota_name}{'开启' if data.enabled else '关闭'}成功",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def apply_create(self, operator: dict, data: QuotaApplyCreateSchema):
        operator_user = self.user_repo.get_by_id(operator.get("user_id"))
        if operator_user and operator_user.user_type == "internal":
            if not data.member_id:
                raise BusinessException(code=ErrorCode.FAILED, message="member_id不能为空")
            member = self.member_repo.get_active_by_id(data.member_id)
        else:
            member = self.member_repo.get_active_by_id(self._resolve_member_for_user(operator.get("user_id")).id)
        if not member:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="会员不存在或已冻结")
        category = self.repo.get_category_by_code(data.quota_code)
        if not category:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="配额类别不存在")
        if not category.enabled:
            raise BusinessException(code=ErrorCode.FAILED, message="当前配额类别未启用")
        member_quota = self.repo.get_member_quota(member.id, data.cloud_provider_code, data.quota_code)
        allocated_quota = Decimal(str(member_quota.allocated_quota if member_quota else 0)).quantize(
            Decimal("0.00"), rounding=ROUND_HALF_UP
        )
        payload = {
            "member_id": member.id,
            "cloud_provider_code": data.cloud_provider_code,
            "resource_type": category.resource_type,
            "quota_name": category.quota_name,
            "quota_code": category.quota_code,
            "quantity_type": category.quantity_type,
            "allocated_quota": allocated_quota,
            "apply_quota": Decimal(str(data.apply_quota)).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP),
            "apply_remark": data.apply_remark,
            "approve_status": "PENDING",
            "created_by": operator.get("user_id"),
            "created_by_name": operator.get("username"),
        }
        try:
            apply_obj = self.repo.create_apply(payload)
            self.cmp_db.commit()
            self._write_quota_audit_log(
                operator,
                ActionOperate.CREATE.value,
                str(apply_obj.id),
                f"配额申请已提交，会员：{member.member_name}，配额：{category.quota_name}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def apply_page_list(
        self,
        page: int,
        page_size: int,
        cloud_provider_code: str = None,
        quantity_type: str = None,
        enabled: bool = None,
        approve_status: str = None,
    ):
        items, total = self.repo.apply_page_list(page, page_size, cloud_provider_code, quantity_type, enabled, approve_status)
        return QuotaApplyPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[QuotaApplyOutSchema.model_validate(item._asdict()) for item in items],
        )

    def apply_approve(self, operator: dict, data: QuotaApplyApproveSchema):
        self._require_internal(operator)
        apply_obj = self.repo.get_apply(data.apply_id)
        if not apply_obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if apply_obj.approve_status != "PENDING":
            raise BusinessException(code=ErrorCode.FAILED, message="该申请已处理")

        member_quota = self.repo.get_member_quota(
            apply_obj.member_id, apply_obj.cloud_provider_code, apply_obj.quota_code
        )
        if not member_quota:
            member_quota = MemberQuota(
                member_id=apply_obj.member_id,
                cloud_provider_code=apply_obj.cloud_provider_code,
                resource_type=apply_obj.resource_type,
                quota_name=apply_obj.quota_name,
                quota_code=apply_obj.quota_code,
                allocated_quota=apply_obj.apply_quota,
                created_by=operator.get("user_id"),
                created_by_name=operator.get("username"),
            )
        else:
            member_quota.allocated_quota = apply_obj.apply_quota

        apply_obj.approve_status = "APPROVED"
        apply_obj.approved_by = operator.get("user_id")
        apply_obj.approved_by_name = operator.get("username")
        apply_obj.approve_remark = data.approve_remark
        from datetime import datetime
        apply_obj.approved_at = datetime.utcnow()
        try:
            self.repo.save_member_quota(member_quota)
            self.cmp_db.commit()
            self._write_quota_audit_log(
                operator,
                ActionOperate.APPROVE.value,
                str(apply_obj.id),
                f"配额审批通过，配额：{apply_obj.quota_name}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def apply_reject(self, operator: dict, data: QuotaApplyRejectSchema):
        self._require_internal(operator)
        apply_obj = self.repo.get_apply(data.apply_id)
        if not apply_obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if apply_obj.approve_status != "PENDING":
            raise BusinessException(code=ErrorCode.FAILED, message="该申请已处理")

        apply_obj.approve_status = "REJECTED"
        apply_obj.approved_by = operator.get("user_id")
        apply_obj.approved_by_name = operator.get("username")
        apply_obj.approve_remark = data.approve_remark
        from datetime import datetime
        apply_obj.approved_at = datetime.utcnow()
        try:
            self.cmp_db.commit()
            self._write_quota_audit_log(
                operator,
                ActionOperate.REJECT.value,
                str(apply_obj.id),
                f"配额审批驳回，配额：{apply_obj.quota_name}",
            )
            return True
        except Exception:
            self.cmp_db.rollback()
            raise
