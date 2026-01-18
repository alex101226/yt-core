# app/services/stat_service.py
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.cmp import AuditLog
from app.repositories.cmp.stat_repo import StatRepository

from app.constants.enums import ActionOperate, ActionMode

from app.schemas.cmp.state_schema import AuditLogSchema

class StatService:

    def __init__(self, db: Session):
        self.repo = StatRepository(db)

    # 首页，资源信息统计
    def get_user_statistics(self, user_id: int) -> dict:
        return {
            "servers": self.repo.count_servers(user_id),
            "vpcs": self.repo.count_vpcs(user_id),
            "subnets": self.repo.count_subnets(user_id),
            "security_groups": self.repo.count_security_groups(user_id),
            "disks": self.repo.count_disks(user_id),
            "cephfs": self.repo.count_cephfs(user_id),
            "gpfs": self.repo.count_gpfs(user_id),
            "clusters": self.repo.count_clusters(user_id),
            "container_images": self.repo.count_container_images(user_id),
        }

    # 用户资金支出
    def get_monthly_stats(self, user_id: int) -> dict:
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        # year = now.year
        # month = now.month
        billing_period = f"{year}-{month:02d}"

        return {
            "spent_amount": self.repo.sum_monthly_spent(user_id, year, month),
            "invoice_amount": self.repo.sum_monthly_invoice_amount(user_id, billing_period),
            "credit_amount": self.repo.sum_monthly_credit(user_id, year, month),
            "voucher_amount": self.repo.sum_monthly_voucher(user_id, year, month)
        }

    # 创建一条系统通知（操作日志）
    def create_notification(self, data: AuditLogSchema):
        return self.repo.create_notification(**data.model_dump())

    # 获取通知列表
    def get_notifications_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> dict:
        return self.repo.list_notifications(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )

    # 获取未读通知数量
    def get_unread_notification_count(self, user_id: int) -> int:
        return self.repo.count_unread_notifications(user_id)

    # 标记单条通知已读
    def mark_notification_read(self, user_id: int, log_id: int) -> bool:
        return self.repo.mark_notification_read(
            user_id=user_id,
            log_id=log_id
        )

    # 全部标记已读
    def mark_all_notifications_read(self, user_id: int) -> int:
        return self.repo.mark_all_notifications_read(user_id=user_id)