# app/repositories/stat_repo.py
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp import (
    CloudServerInstance, Vpc, Subnet, SecurityGroup,
    CbsDisk, CephfsFile, GPFSFile, K8sCluster, ImageRepository, AuditLog
)
from app.constants.enums import ActionMode, ActionOperate

class StatRepository:

    def __init__(self, db: Session):
        self.db = db

    def count_servers(self, user_id: int) -> int:
        return self.db.query(CloudServerInstance).filter(CloudServerInstance.created_by == user_id).count()

    def count_vpcs(self, user_id: int) -> int:
        return self.db.query(Vpc).filter(Vpc.created_by == user_id).count()

    def count_subnets(self, user_id: int) -> int:
        return self.db.query(Subnet).filter(Subnet.user_id == user_id).count()

    def count_security_groups(self, user_id: int) -> int:
        return self.db.query(SecurityGroup).filter(SecurityGroup.created_by == user_id).count()

    def count_disks(self, user_id: int) -> int:
        return self.db.query(CbsDisk).filter(CbsDisk.user_id == user_id).count()

    def count_cephfs(self, user_id: int) -> int:
        return self.db.query(CephfsFile).filter(CephfsFile.user_id == user_id).count()

    def count_gpfs(self, user_id: int) -> int:
        return self.db.query(GPFSFile).filter(GPFSFile.created_by == user_id).count()

    def count_clusters(self, user_id: int) -> int:
        return self.db.query(K8sCluster).filter(K8sCluster.created_by == user_id).count()

    def count_container_images(self, user_id: int) -> int:
        return self.db.query(ImageRepository).filter(ImageRepository.created_by == user_id).count()

    # 月支出
    def sum_monthly_spent(self, user_id: int, year: int, month: int) -> float:
        from app.models.cmp.funds_flow import FundsFlow
        total = self.db.query(func.sum(FundsFlow.amount)) \
            .filter(
            FundsFlow.user_id == user_id,
            FundsFlow.direction == 'OUT',
            FundsFlow.flow_type == 'PAY_ORDER',
            extract('year', FundsFlow.created_at) == year,
            extract('month', FundsFlow.created_at) == month
        ).scalar()
        return float(total or 0)

    # 可开发票金额
    def sum_monthly_invoice_amount(self, user_id: int, billing_period: str) -> float:
        from app.models.cmp.invoice_item import InvoiceItem
        total = self.db.query(func.sum(InvoiceItem.invoice_amount)) \
            .filter(
            InvoiceItem.user_id == user_id,
            InvoiceItem.status == 'UNISSUED',
            InvoiceItem.billing_period == billing_period
        ).scalar()
        return float(total or 0)

    # 抵佣金
    def sum_monthly_credit(self, user_id: int, year: int, month: int) -> float:
        from app.models.cmp.order_detail import OrderDetail
        from app.models.cmp.order import Order
        total = self.db.query(func.sum(OrderDetail.credit_amount)) \
            .join(Order, OrderDetail.order_id == Order.id) \
            .filter(
            Order.created_by == user_id,
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ).scalar()
        return float(total or 0)

    # 代金券
    def sum_monthly_voucher(self, user_id: int, year: int, month: int) -> float:
        from app.models.cmp.order_detail import OrderDetail
        from app.models.cmp.order import Order
        total = self.db.query(func.sum(OrderDetail.voucher_amount)) \
            .join(Order, OrderDetail.order_id == Order.id) \
            .filter(
            Order.created_by == user_id,
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ).scalar()
        return float(total or 0)


    # 系统通知（用户操作日志）
    def create_notification(self, **kwargs) -> AuditLog:
        log = AuditLog(**kwargs)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    # 获取当前用户的通知列表
    def list_notifications(
        self,
        *,
        user_id: int,
        page: int = 1,
        page_size: int = 10,
    ):
        query = self.db.query(AuditLog).filter(
            AuditLog.operate_id == user_id,
            AuditLog.is_read.is_(False)
        )

        total = query.count()

        records = (
            query
            .order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "items": records,
            "page": page,
            "page_size": page_size,
        }

    # 未读通知数量
    def count_unread_notifications(self, user_id: int) -> int:
        return (
            self.db.query(func.count(AuditLog.id))
            .filter(
                AuditLog.operate_id == user_id,
                AuditLog.is_read.is_(False)
            )
            .scalar()
        )

    # 标记单条通知已读
    def mark_notification_read(self, *, user_id: int, log_id: int) -> bool:
        updated = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.id == log_id,
                AuditLog.operate_id == user_id,
                AuditLog.is_read.is_(False)
            )
            .update(
                {
                    AuditLog.is_read: True,
                    AuditLog.read_at: datetime.now(timezone.utc)
                },
                synchronize_session=False
            )
        )
        return updated > 0

    # 一键全部已读
    def mark_all_notifications_read(self, *, user_id: int) -> int:
        return (
            self.db.query(AuditLog)
            .filter(
                AuditLog.operate_id == user_id,
                AuditLog.is_read.is_(False)
            )
            .update(
                {
                    AuditLog.is_read: True,
                    AuditLog.read_at: datetime.now(timezone.utc)
                },
                synchronize_session=False
            )
        )
