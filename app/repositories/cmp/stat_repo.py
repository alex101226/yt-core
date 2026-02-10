# app/repositories/stat_repo.py
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, extract, desc, case
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp import (
    CloudServerInstance, Vpc, Subnet, SecurityGroup, CbsDisk, CephfsFile, GPFSFile,
    K8sCluster, ImageRepository, AuditLog, Account, OrderDetail, Order, InvoiceRecord,
    InvoiceItem, FundsFlow, BareMetalInstance
)

class StatRepository:

    def __init__(self, db: Session):
        self.db = db
    # 裸金属的数量
    def count_bares(self, user_id: int):
        return self.db.query(BareMetalInstance).filter(BareMetalInstance.created_by == user_id).count()

    # 服务器数量
    def count_servers(self, user_id: int) -> int:
        return self.db.query(CloudServerInstance).filter(CloudServerInstance.created_by == user_id).count()

    # vpc数量
    def count_vpcs(self, user_id: int) -> int:
        return self.db.query(Vpc).filter(Vpc.created_by == user_id).count()

    # 子网数量
    def count_subnets(self, user_id: int) -> int:
        return self.db.query(Subnet).filter(Subnet.created_by == user_id).count()

    # 安全组数量
    def count_security_groups(self, user_id: int) -> int:
        return self.db.query(SecurityGroup).filter(SecurityGroup.created_by == user_id).count()

    # cbs数量
    def count_disks(self, user_id: int) -> int:
        return self.db.query(CbsDisk).filter(CbsDisk.created_by == user_id).count()

    # cephfs数量
    def count_cephfs(self, user_id: int) -> int:
        return self.db.query(CephfsFile).filter(CephfsFile.created_by == user_id).count()

    # gpfs数量
    def count_gpfs(self, user_id: int) -> int:
        return self.db.query(GPFSFile).filter(GPFSFile.created_by == user_id).count()

    # 集群数量
    def count_clusters(self, user_id: int) -> int:
        return self.db.query(K8sCluster).filter(K8sCluster.created_by == user_id).count()

    # 容器镜像数量
    def count_container_images(self, user_id: int) -> int:
        return self.db.query(ImageRepository).filter(ImageRepository.created_by == user_id).count()
    # 物理的状态统计
    def stat_baremetal_status(self, user_id: int):
        return (
            self.db.query(
                func.sum(
                    case((BareMetalInstance.status == 'RUNNING', 1), else_=0)
                ).label('running'),
                func.sum(
                    case((BareMetalInstance.status == 'STOPPED', 1), else_=0)
                ).label('stopped'),
                func.sum(
                    case((BareMetalInstance.status.in_(['ERROR', 'FAILED']), 1), else_=0)
                ).label('error'),
            ).filter(
                BareMetalInstance.created_by == user_id,
                BareMetalInstance.is_released == 0
            ).one()
        )
    # 服务器的状态统计
    def state_server_status(self, user_id: int):
        return self.db.query(
            func.sum(
                case((CloudServerInstance.status == 'RUNNING', 1), else_=0)
            ).label('running'),
            func.sum(
                case((CloudServerInstance.status == 'STOPPED', 1), else_=0)
            ).label('stopped'),
            func.sum(
                case((CloudServerInstance.status.in_(['ERROR', 'FAILED']), 1), else_=0)
            ).label('error'),
        ).filter(
            CloudServerInstance.created_by == user_id,
            CloudServerInstance.is_released == 0
        ).one()

    # 纳管，历史的gpu算力
    def total_compute(self, user_id: int, isAll: bool = False):
        GPU_FLOPS_MAP = {
            "NVIDIA A10": 125,
            "NVIDIA A100": 312,
            "NVIDIA H1000": 1000,
        }
        query1 = self.db.query(
                BareMetalInstance.gpu_amount,
                BareMetalInstance.gpu_spec
            )

        query2 = self.db.query(
                CloudServerInstance.gpu_amount,
                CloudServerInstance.gpu_spec
            )
        filters1 = [BareMetalInstance.created_by == user_id, BareMetalInstance.gpu_amount > 0]
        filters2 = [CloudServerInstance.created_by == user_id, CloudServerInstance.gpu_amount > 0]
        if not isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)
        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        total_tflops = 0

        for gpu_amount, gpu_spec in bare + cloud:
            tflops = GPU_FLOPS_MAP.get(gpu_spec, 0)
            total_tflops += gpu_amount * tflops
        return round(total_tflops / 1000, 2)

    # 纳管，gpu量
    def total_gpu_amount(self, user_id: int, isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.gpu_amount)
        query2 = self.db.query(CloudServerInstance.gpu_amount)

        filters1 = [
            BareMetalInstance.created_by == user_id,
            BareMetalInstance.gpu_amount > 0
        ]
        filters2 = [
            CloudServerInstance.created_by == user_id,
            CloudServerInstance.gpu_amount > 0
        ]

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        total = sum(x[0] for x in bare + cloud)
        return total

    # 纳管，cpu量
    def total_cpu(self, user_id: int, isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.cpu)
        query2 = self.db.query(CloudServerInstance.cpu)

        filters1 = [
            BareMetalInstance.created_by == user_id,
            BareMetalInstance.cpu > 0
        ]
        filters2 = [
            CloudServerInstance.created_by == user_id,
            CloudServerInstance.cpu > 0
        ]

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        return sum(x[0] for x in bare + cloud)

    # 纳管，内存
    def total_memory(self, user_id: int, isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.system_disk_size)
        query2 = self.db.query(CloudServerInstance.system_disk_size)

        filters1 = [
            BareMetalInstance.created_by == user_id,
            BareMetalInstance.system_disk_size > 0
        ]
        filters2 = [
            CloudServerInstance.created_by == user_id,
            CloudServerInstance.system_disk_size > 0
        ]

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        return sum(x[0] for x in bare + cloud)

    # 纳管，存储
    def total_storage(self, user_id: int, isAll: bool = False):
        query1 = self.db.query(CbsDisk.disk_size)

        filters1 = [
            CbsDisk.created_by == user_id,
            CbsDisk.disk_size > 0
        ]

        if isAll:
            filters1.append(CbsDisk.is_released == 0)

        cbs = query1.filter(*filters1).all()

        return sum(x[0] for x in cbs)

    # 纳管gpu分配率
    def current_gpu_rate_by_provider(self, user_id: int):
        # 运行中的 GPU
        running_bare = (
            self.db.query(
                BareMetalInstance.cloud_provider_code,
                func.sum(BareMetalInstance.gpu_amount)
            )
            .filter(
                BareMetalInstance.created_by == user_id,
                BareMetalInstance.is_released == 0,
                BareMetalInstance.status == 'RUNNING',
                BareMetalInstance.gpu_amount > 0
            )
            .group_by(BareMetalInstance.cloud_provider_code)
            .all()
        )
        # 纳管中的 GPU 总量
        total_bare = (
            self.db.query(
                BareMetalInstance.cloud_provider_code,
                func.sum(BareMetalInstance.gpu_amount)
            )
            .filter(
                BareMetalInstance.created_by == user_id,
                BareMetalInstance.is_released == 0,
                BareMetalInstance.gpu_amount > 0
            )
            .group_by(BareMetalInstance.cloud_provider_code)
            .all()
        )


        running_cloud = (
            self.db.query(
                CloudServerInstance.cloud_provider_code,
                func.sum(CloudServerInstance.gpu_amount)
            )
            .filter(
                CloudServerInstance.created_by == user_id,
                CloudServerInstance.is_released == 0,
                CloudServerInstance.status == 'RUNNING',
                CloudServerInstance.gpu_amount > 0
            )
            .group_by(CloudServerInstance.cloud_provider_code)
            .all()
        )



        total_cloud = (
            self.db.query(
                CloudServerInstance.cloud_provider_code,
                func.sum(CloudServerInstance.gpu_amount)
            )
            .filter(
                CloudServerInstance.created_by == user_id,
                CloudServerInstance.is_released == 0,
                CloudServerInstance.gpu_amount > 0
            )
            .group_by(CloudServerInstance.cloud_provider_code)
            .all()
        )

        def merge(rows):
            data = {}
            for k, v in rows:
                data[k] = data.get(k, 0) + (v or 0)
            return data

        running = merge(running_bare + running_cloud)
        total = merge(total_bare + total_cloud)

        rates = {}
        for provider in total:
            if total[provider] == 0:
                rates[provider] = 0
            else:
                rates[provider] = round(running.get(provider, 0) / total[provider] * 100, 2)

        return rates

    # 当月支出
    def sum_monthly_spent(self, user_id: int, year: int, month: int) -> float:
        total = self.db.query(func.sum(FundsFlow.amount)) \
            .filter(
            FundsFlow.created_by == user_id,
            FundsFlow.direction == 'OUT',
            FundsFlow.flow_type == 'PAY_ORDER',
            extract('year', FundsFlow.created_at) == year,
            extract('month', FundsFlow.created_at) == month
        ).scalar()
        return float(total or 0)

    # 当月收入
    def sum_monthly_income(self, user_id: int, year: int, month: int) -> float:
        total = self.db.query(func.sum(FundsFlow.amount)) \
            .filter(
            FundsFlow.created_by == user_id,
            FundsFlow.direction == 'IN',
            extract('year', FundsFlow.created_at) == year,
            extract('month', FundsFlow.created_at) == month
        ).scalar()

        return float(total or 0)

    # 可开发票金额
    def sum_monthly_invoice_amount(self, user_id: int, billing_period: Optional[str]=None) -> float:
        query = self.db.query(func.sum(InvoiceItem.invoice_amount)) \
            .filter(
            InvoiceItem.created_by == user_id,
            InvoiceItem.status == 'UNISSUED'
        )
        if billing_period:
            query = query.filter(
                InvoiceItem.billing_period == billing_period
            )

        total = query.scalar()
        return float(total or 0)

    # 已开票金额
    def sum_monthly_invoiced_amount(
        self,
        user_id: int,
        billing_period: Optional[str]=None
    ) -> float:
        query = self.db.query(func.sum(InvoiceRecord.amount)) \
            .filter(
            InvoiceRecord.created_by == user_id,
            InvoiceRecord.status == 'ISSUED'
        )

        if billing_period:
            query = query.filter(
                InvoiceItem.billing_period == billing_period
            )
        total = query.scalar()
        return float(total or 0)

    # 抵佣金
    def sum_monthly_credit(self, user_id: int, year: int, month: int) -> float:
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
        total = self.db.query(func.sum(OrderDetail.voucher_amount)) \
            .join(Order, OrderDetail.order_id == Order.id) \
            .filter(
            Order.created_by == user_id,
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ).scalar()
        return float(total or 0)

    # 账户可用金额
    def get_available_quota(self, user_id: int) -> float:
        query = self.db.query(Account.balance).filter(Account.created_by == user_id)
        # if year and month:
        #     return query.filter(
        #         extract('year', FundsFlow.created_at) == year,
        #         extract('month', FundsFlow.created_at) == month
        #     ).scalar()

        query = query.scalar()
        return float(query or 0)

    # 当月订单数
    def count_monthly_orders(self, user_id: int, year: int, month: int) -> int:
        total = self.db.query(func.count(Order.id)) \
            .filter(
            Order.created_by == user_id,
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ).scalar()

        return int(total or 0)

    """
    field_name: 'cloud_provider_code' / 'product_name' / 'business_name'
    """
    def top5_by_field(self, user_id: int, year: int, month: int, field_name: str):
        # 总金额
        total_amount = self.db.query(func.sum(Order.amount_payable)) \
                           .filter(
            Order.created_by == user_id,
            Order.pay_status == 'SUCCESS',
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ).scalar() or 0

        if total_amount == 0:
            return []

        # 每个名称的金额汇总
        rows = self.db.query(
            getattr(Order, field_name).label("name"),
            func.sum(Order.amount_payable).label("amount")
        ) \
            .filter(
            Order.created_by == user_id,
            Order.pay_status == 'SUCCESS',
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        ) \
            .group_by(getattr(Order, field_name)) \
            .order_by(desc("amount")) \
            .limit(5) \
            .all()

        # 计算比例
        result = [
            {
                "name": r.name,
                "amount": round(float(r.amount), 2),
                "ratio": round(float(r.amount / total_amount), 2)
            } for r in rows
        ]
        return result

    # 系统通知（用户操作日志）
    def create_notification(self, **kwargs) -> AuditLog:
        logger.info(f'能执行过来吗？')
        log = AuditLog(**kwargs)
        self.db.add(log)
        # self.db.flush()
        # self.db.commit()
        # self.db.refresh(log)
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
            AuditLog.created_by == user_id,
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
                AuditLog.created_by == user_id,
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
                AuditLog.created_by == user_id,
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
        if updated > 0:
            self.db.commit()  # ✅ 提交事务
            return True
        return False

    # 一键全部已读
    def mark_all_notifications_read(self, *, user_id: int) -> int:
        updated_count = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.created_by == user_id,
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

        if updated_count > 0:
            self.db.commit()  # ✅ 提交事务
        return updated_count
