# app/repositories/stat_repo.py
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import func, extract, desc, case, and_, or_
from sqlalchemy.orm import Session

from app.constants.billing_meta import BILLING_META_MAP
from app.constants.enums import BillingStatus, ResourceType
from app.core.logger import logger
from app.models.cmp import (
    CloudServerInstance, Vpc, Subnet, SecurityGroup, CbsDisk, CephfsFile, GPFSFile,
    K8sCluster, ImageRepository, AuditLog, Account, OrderDetail, Order, InvoiceRecord,
    InvoiceItem, FundsFlow, BareMetalInstance, CloudImage, Eip, OssBucket, LoadBalancer,
    Member, VoucherAssign, VoucherTemplate, CreditGrant, QuotaApply, BillingInstance
)
from app.constants.enums import Direction, FlowType

class StatRepository:

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _append_user_filter(filters: list, column, user_id: Optional[int]):
        if user_id is not None:
            filters.append(column == user_id)
        return filters
    # 裸金属的数量
    def count_bares(self, user_id: Optional[int] = None):
        query = self.db.query(BareMetalInstance)
        if user_id is not None:
            query = query.filter(BareMetalInstance.created_by == user_id)
        return query.count()

    # 服务器数量
    def count_servers(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(CloudServerInstance)
        if user_id is not None:
            query = query.filter(CloudServerInstance.created_by == user_id)
        return query.count()

    # vpc数量
    def count_vpcs(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(Vpc)
        if user_id is not None:
            query = query.filter(Vpc.created_by == user_id)
        return query.count()

    # 子网数量
    def count_subnets(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(Subnet)
        if user_id is not None:
            query = query.filter(Subnet.created_by == user_id)
        return query.count()

    # 安全组数量
    def count_security_groups(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(SecurityGroup)
        if user_id is not None:
            query = query.filter(SecurityGroup.created_by == user_id)
        return query.count()

    # cbs数量
    def count_disks(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(CbsDisk)
        if user_id is not None:
            query = query.filter(CbsDisk.created_by == user_id)
        return query.count()

    # cephfs数量
    def count_cephfs(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(CephfsFile)
        if user_id is not None:
            query = query.filter(CephfsFile.created_by == user_id)
        return query.count()

    # gpfs数量
    def count_gpfs(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(GPFSFile)
        if user_id is not None:
            query = query.filter(GPFSFile.created_by == user_id)
        return query.count()

    # 集群数量
    def count_clusters(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(K8sCluster)
        if user_id is not None:
            query = query.filter(K8sCluster.created_by == user_id)
        return query.count()

    # 容器镜像数量
    def count_container_images(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(ImageRepository)
        if user_id is not None:
            query = query.filter(ImageRepository.created_by == user_id)
        return query.count()

    # 自定义系统镜像数量
    def count_cloud_images(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(CloudImage)
        if user_id is not None:
            query = query.filter(CloudImage.created_by == user_id)
        return query.count()

    # 负载均衡数量
    def count_load_balancers(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(LoadBalancer)
        if user_id is not None:
            query = query.filter(LoadBalancer.created_by == user_id)
        return query.count()

    # 弹性公网IP数量
    def count_eips(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(Eip)
        if user_id is not None:
            query = query.filter(Eip.created_by == user_id)
        return query.count()

    # OSS对象存储数量
    def count_oss(self, user_id: Optional[int] = None) -> int:
        query = self.db.query(OssBucket)
        if user_id is not None:
            query = query.filter(OssBucket.created_by == user_id)
        return query.count()

    def operation_income_summary(self, now: datetime, owner_user_id: Optional[int] = None) -> dict:
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        income_filter = (
            FundsFlow.direction == Direction.IN,
            FundsFlow.is_released == 0,
        )

        query = self.db.query(
            func.coalesce(
                func.sum(case((FundsFlow.created_at >= start_today, FundsFlow.amount), else_=0)),
                0,
            ).label("today_amount"),
            func.coalesce(
                func.sum(case((FundsFlow.created_at >= start_month, FundsFlow.amount), else_=0)),
                0,
            ).label("month_amount"),
            func.coalesce(
                func.sum(case((FundsFlow.created_at >= start_year, FundsFlow.amount), else_=0)),
                0,
            ).label("year_amount"),
        ).filter(*income_filter)
        if owner_user_id is not None:
            query = query.filter(FundsFlow.created_by == owner_user_id)
        row = query.one()

        return {
            "today_amount": float(row.today_amount or 0),
            "month_amount": float(row.month_amount or 0),
            "year_amount": float(row.year_amount or 0),
        }

    def operation_pending_counts(self, member_id: Optional[int] = None) -> dict:
        credit_pending = (
            self.db.query(func.count(CreditGrant.id))
            .filter(
                CreditGrant.approve_status == "PENDING",
                CreditGrant.is_released == 0,
                *( [CreditGrant.member_id == member_id] if member_id is not None else [] ),
            )
            .scalar()
            or 0
        )
        quota_pending = (
            self.db.query(func.count(QuotaApply.id))
            .filter(
                QuotaApply.approve_status == "PENDING",
                QuotaApply.is_released == 0,
            )
            .scalar()
            or 0
        )
        return {
            "approval_task_count": int(credit_pending + quota_pending),
            "quota_apply_count": int(quota_pending),
        }

    def operation_voucher_summary(self, now: datetime, member_id: Optional[int] = None) -> dict:
        total_query = (
            self.db.query(func.coalesce(func.sum(VoucherTemplate.amount * VoucherAssign.quantity), 0))
            .select_from(VoucherAssign)
            .join(VoucherTemplate, VoucherTemplate.id == VoucherAssign.template_id)
            .filter(
                VoucherAssign.is_released == 0,
                VoucherTemplate.is_released == 0,
            )
        )
        expired_query = (
            self.db.query(func.coalesce(func.sum(VoucherTemplate.amount * VoucherAssign.quantity), 0))
            .select_from(VoucherAssign)
            .join(VoucherTemplate, VoucherTemplate.id == VoucherAssign.template_id)
            .filter(
                VoucherAssign.is_released == 0,
                VoucherTemplate.is_released == 0,
                VoucherAssign.valid_end < now,
            )
        )
        if member_id is not None:
            total_query = total_query.filter(VoucherAssign.member_id == member_id)
            expired_query = expired_query.filter(VoucherAssign.member_id == member_id)
        total_distributed = total_query.scalar() or 0

        expired_amount = expired_query.scalar() or 0

        consumed_query = (
            self.db.query(func.coalesce(func.sum(OrderDetail.voucher_amount), 0))
            .join(Order, Order.id == OrderDetail.order_id)
            .filter(
                Order.is_released == 0,
                Order.pay_status == "SUCCESS",
            )
        )
        if member_id is not None:
            consumed_query = consumed_query.outerjoin(Member, Member.user_id == Order.created_by).filter(Member.id == member_id)
        consumed_amount = consumed_query.scalar() or 0

        current_remaining = max(float(total_distributed or 0) - float(expired_amount or 0) - float(consumed_amount or 0), 0)
        return {
            "distributed_amount": float(total_distributed or 0),
            "expired_amount": float(expired_amount or 0),
            "current_remaining": current_remaining,
        }

    def operation_credit_summary(self, now: datetime, member_id: Optional[int] = None) -> dict:
        query = self.db.query(
            func.coalesce(
                func.sum(
                    case(
                        (
                            (CreditGrant.approve_status == "APPROVED") &
                            (CreditGrant.is_released == 0),
                            CreditGrant.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("distributed_amount"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (CreditGrant.approve_status == "APPROVED") &
                            (CreditGrant.is_released == 0) &
                            (CreditGrant.valid_end < now),
                            CreditGrant.remaining_amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("expired_amount"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (CreditGrant.approve_status == "APPROVED") &
                            (CreditGrant.is_released == 0) &
                            (CreditGrant.valid_start <= now) &
                            (CreditGrant.valid_end >= now) &
                            (CreditGrant.status == "ACTIVE"),
                            CreditGrant.remaining_amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("current_remaining"),
        )
        if member_id is not None:
            query = query.filter(CreditGrant.member_id == member_id)
        row = query.one()

        return {
            "distributed_amount": float(row.distributed_amount or 0),
            "expired_amount": float(row.expired_amount or 0),
            "current_remaining": float(row.current_remaining or 0),
        }

    def operation_member_count(self, member_id: Optional[int] = None) -> int:
        query = self.db.query(func.count(Member.id)).filter(Member.is_released == 0)
        if member_id is not None:
            query = query.filter(Member.id == member_id)
        return int(query.scalar() or 0)

    def _order_time_filters(
        self,
        start_at: datetime,
        end_at: datetime,
        cloud_provider_code: Optional[str] = None,
    ):
        time_col = func.coalesce(Order.paid_at, Order.created_at)
        filters = [
            Order.is_released == 0,
            Order.pay_status == "SUCCESS",
            time_col >= start_at,
            time_col <= end_at,
        ]
        if cloud_provider_code:
            filters.append(Order.cloud_provider_code == cloud_provider_code)
        return filters

    def operation_member_cash_top10(
        self,
        start_at: datetime,
        end_at: datetime,
        cloud_provider_code: Optional[str] = None,
        owner_user_id: Optional[int] = None,
    ):
        filters = self._order_time_filters(start_at, end_at, cloud_provider_code)
        if owner_user_id is not None:
            filters.append(Order.created_by == owner_user_id)

        total_amount = (
            self.db.query(func.coalesce(func.sum(OrderDetail.balance_amount), 0))
            .join(Order, Order.id == OrderDetail.order_id)
            .filter(*filters)
            .scalar()
            or 0
        )

        if not total_amount:
            return []

        name_expr = func.coalesce(Member.member_name, Order.created_by_name)
        rows = (
            self.db.query(
                name_expr.label("name"),
                func.coalesce(func.sum(OrderDetail.balance_amount), 0).label("amount"),
            )
            .join(Order, Order.id == OrderDetail.order_id)
            .outerjoin(Member, Member.user_id == Order.created_by)
            .filter(*filters)
            .group_by(name_expr)
            .order_by(desc("amount"))
            .limit(10)
            .all()
        )

        return [
            {
                "name": row.name or "-",
                "amount": round(float(row.amount or 0), 2),
                "ratio": round(float((row.amount or 0) / total_amount), 4),
            }
            for row in rows
        ]

    def operation_product_consume_top5(
        self,
        start_at: datetime,
        end_at: datetime,
        cloud_provider_code: Optional[str] = None,
        owner_user_id: Optional[int] = None,
    ):
        filters = self._order_time_filters(start_at, end_at, cloud_provider_code)
        if owner_user_id is not None:
            filters.append(Order.created_by == owner_user_id)
        total_amount = (
            self.db.query(func.coalesce(func.sum(Order.amount_payable), 0))
            .filter(*filters)
            .scalar()
            or 0
        )
        if not total_amount:
            return []

        rows = (
            self.db.query(
                Order.product_name.label("name"),
                func.coalesce(func.sum(Order.amount_payable), 0).label("amount"),
            )
            .filter(*filters)
            .group_by(Order.product_name)
            .order_by(desc("amount"))
            .limit(5)
            .all()
        )

        return [
            {
                "name": row.name or "-",
                "amount": round(float(row.amount or 0), 2),
                "ratio": round(float((row.amount or 0) / total_amount), 4),
            }
            for row in rows
        ]

    def operation_cloud_provider_distribution(
        self,
        start_at: datetime,
        end_at: datetime,
        cloud_provider_code: Optional[str] = None,
        owner_user_id: Optional[int] = None,
    ):
        filters = self._order_time_filters(start_at, end_at, cloud_provider_code)
        if owner_user_id is not None:
            filters.append(Order.created_by == owner_user_id)
        total_amount = (
            self.db.query(func.coalesce(func.sum(Order.amount_payable), 0))
            .filter(*filters)
            .scalar()
            or 0
        )
        if not total_amount:
            return []

        rows = (
            self.db.query(
                Order.cloud_provider_code.label("name"),
                func.coalesce(func.sum(Order.amount_payable), 0).label("amount"),
            )
            .filter(*filters)
            .group_by(Order.cloud_provider_code)
            .order_by(desc("amount"))
            .limit(5)
            .all()
        )

        return [
            {
                "name": row.name or "-",
                "amount": round(float(row.amount or 0), 2),
                "ratio": round(float((row.amount or 0) / total_amount), 4),
            }
            for row in rows
        ]

    def operation_unsubscribe_product_top5(
        self,
        start_at: datetime,
        end_at: datetime,
        cloud_provider_code: Optional[str] = None,
        owner_user_id: Optional[int] = None,
    ):
        filters = [
            BillingInstance.is_released == 0,
            BillingInstance.status == BillingStatus.RELEASED,
            BillingInstance.updated_at >= start_at,
            BillingInstance.updated_at <= end_at,
        ]
        if owner_user_id is not None:
            filters.append(BillingInstance.created_by == owner_user_id)
        if cloud_provider_code:
            filters.append(BillingInstance.cloud_provider_code == cloud_provider_code)

        total_count = (
            self.db.query(func.count(BillingInstance.id))
            .filter(*filters)
            .scalar()
            or 0
        )
        if not total_count:
            return []

        rows = (
            self.db.query(
                BillingInstance.resource_type.label("resource_type"),
                func.count(BillingInstance.id).label("amount"),
            )
            .filter(*filters)
            .group_by(BillingInstance.resource_type)
            .order_by(desc("amount"))
            .limit(5)
            .all()
        )

        result = []
        for row in rows:
            resource_type = row.resource_type
            if isinstance(resource_type, str):
                resource_type = ResourceType(resource_type)
            meta = BILLING_META_MAP.get(resource_type)
            result.append(
                {
                    "name": meta.product_name if meta else resource_type.value,
                    "amount": int(row.amount or 0),
                    "ratio": round(float((row.amount or 0) / total_count), 4),
                }
            )
        return result

    def resource_consume_page_list(
        self,
        page: int,
        page_size: int,
        owner_user_id: Optional[int] = None,
        cloud_provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        instance_keyword: Optional[str] = None,
        product_name: Optional[str] = None,
        consume_type: Optional[str] = None,
        member_id: Optional[int] = None,
    ):
        start_time_expr = func.coalesce(Order.paid_at, Order.created_at)
        instance_name_expr = func.coalesce(
            CloudServerInstance.instance_name,
            BareMetalInstance.instance_name,
            CbsDisk.disk_name,
            Eip.eip_name,
            K8sCluster.cluster_name,
            CloudImage.image_name,
            LoadBalancer.lb_name,
            GPFSFile.fs_name,
            CephfsFile.fs_name,
            OssBucket.bucket_name,
            ImageRepository.repository_name,
        )
        member_name_expr = func.coalesce(Member.member_name, Order.created_by_name)

        query = (
            self.db.query(
                Order.id.label("order_id"),
                Order.product_name,
                Order.instance_id,
                instance_name_expr.label("instance_name"),
                start_time_expr.label("start_time"),
                Order.consume_type,
                Order.cloud_provider_code,
                OrderDetail.region.label("region_id"),
                Order.business_name,
                member_name_expr.label("member_name"),
                Order.created_by_name,
            )
            .select_from(Order)
            .join(OrderDetail, OrderDetail.order_id == Order.id)
            .outerjoin(BillingInstance, BillingInstance.id == Order.bill_id)
            .outerjoin(Member, Member.user_id == Order.created_by)
            .outerjoin(
                CloudServerInstance,
                and_(
                    BillingInstance.resource_type == ResourceType.SERVER,
                    BillingInstance.resource_id == CloudServerInstance.id,
                ),
            )
            .outerjoin(
                BareMetalInstance,
                and_(
                    BillingInstance.resource_type == ResourceType.BAREMETAL,
                    BillingInstance.resource_id == BareMetalInstance.id,
                ),
            )
            .outerjoin(
                CbsDisk,
                and_(
                    BillingInstance.resource_type == ResourceType.DISK,
                    BillingInstance.resource_id == CbsDisk.id,
                ),
            )
            .outerjoin(
                Eip,
                and_(
                    BillingInstance.resource_type == ResourceType.EIP,
                    BillingInstance.resource_id == Eip.id,
                ),
            )
            .outerjoin(
                K8sCluster,
                and_(
                    BillingInstance.resource_type == ResourceType.CLUSTER,
                    BillingInstance.resource_id == K8sCluster.id,
                ),
            )
            .outerjoin(
                CloudImage,
                and_(
                    BillingInstance.resource_type == ResourceType.CUSTOM_IMAGE,
                    BillingInstance.resource_id == CloudImage.id,
                ),
            )
            .outerjoin(
                LoadBalancer,
                and_(
                    BillingInstance.resource_type == ResourceType.LOAD_INSTANCE,
                    BillingInstance.resource_id == LoadBalancer.id,
                ),
            )
            .outerjoin(
                GPFSFile,
                and_(
                    BillingInstance.resource_type == ResourceType.GPFS,
                    BillingInstance.resource_id == GPFSFile.id,
                ),
            )
            .outerjoin(
                CephfsFile,
                and_(
                    BillingInstance.resource_type == ResourceType.CEPHFS,
                    BillingInstance.resource_id == CephfsFile.id,
                ),
            )
            .outerjoin(
                OssBucket,
                and_(
                    BillingInstance.resource_type == ResourceType.OSS,
                    BillingInstance.resource_id == OssBucket.id,
                ),
            )
            .outerjoin(
                ImageRepository,
                and_(
                    BillingInstance.resource_type == ResourceType.CONTAINER_IMAGE,
                    BillingInstance.resource_id == ImageRepository.id,
                ),
            )
            .filter(
                Order.is_released == 0,
                Order.pay_status == "SUCCESS",
            )
        )
        if owner_user_id is not None:
            query = query.filter(Order.created_by == owner_user_id)

        if cloud_provider_code:
            query = query.filter(Order.cloud_provider_code == cloud_provider_code)
        if region_id:
            query = query.filter(OrderDetail.region == region_id)
        if product_name:
            query = query.filter(Order.product_name == product_name)
        if consume_type:
            query = query.filter(Order.consume_type == consume_type)
        if member_id:
            query = query.filter(Member.id == member_id)
        if instance_keyword:
            like_value = f"%{instance_keyword}%"
            query = query.filter(
                or_(
                    Order.instance_id.like(like_value),
                    instance_name_expr.like(like_value),
                )
            )

        total = query.count()
        items = (
            query
            .order_by(desc(start_time_expr), desc(Order.id))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
    # 物理的状态统计
    def stat_baremetal_status(self, user_id: Optional[int] = None):
        query = self.db.query(
                func.sum(
                    case((BareMetalInstance.status == 'RUNNING', 1), else_=0)
                ).label('running'),
                func.sum(
                    case((BareMetalInstance.status == 'STOPPED', 1), else_=0)
                ).label('stopped'),
                func.sum(
                    case((BareMetalInstance.status.in_(['ERROR', 'FAILED']), 1), else_=0)
                ).label('error'),
            ).filter(BareMetalInstance.is_released == 0)
        if user_id is not None:
            query = query.filter(BareMetalInstance.created_by == user_id)
        return query.one()
    # 服务器的状态统计
    def state_server_status(self, user_id: Optional[int] = None):
        query = self.db.query(
            func.sum(
                case((CloudServerInstance.status == 'RUNNING', 1), else_=0)
            ).label('running'),
            func.sum(
                case((CloudServerInstance.status == 'STOPPED', 1), else_=0)
            ).label('stopped'),
            func.sum(
                case((CloudServerInstance.status.in_(['ERROR', 'FAILED']), 1), else_=0)
            ).label('error'),
        ).filter(CloudServerInstance.is_released == 0)
        if user_id is not None:
            query = query.filter(CloudServerInstance.created_by == user_id)
        return query.one()

    # 纳管，历史的gpu算力
    def total_compute(self, user_id: Optional[int], isAll: bool = False):
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
        filters1 = [BareMetalInstance.gpu_amount > 0]
        filters2 = [CloudServerInstance.gpu_amount > 0]
        if user_id is not None:
            filters1.append(BareMetalInstance.created_by == user_id)
            filters2.append(CloudServerInstance.created_by == user_id)
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
    def total_gpu_amount(self, user_id: Optional[int], isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.gpu_amount)
        query2 = self.db.query(CloudServerInstance.gpu_amount)

        filters1 = [BareMetalInstance.gpu_amount > 0]
        filters2 = [CloudServerInstance.gpu_amount > 0]
        if user_id is not None:
            filters1.append(BareMetalInstance.created_by == user_id)
            filters2.append(CloudServerInstance.created_by == user_id)

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        total = sum(x[0] for x in bare + cloud)
        return total

    # 纳管，cpu量
    def total_cpu(self, user_id: Optional[int], isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.cpu)
        query2 = self.db.query(CloudServerInstance.cpu)

        filters1 = [BareMetalInstance.cpu > 0]
        filters2 = [CloudServerInstance.cpu > 0]
        if user_id is not None:
            filters1.append(BareMetalInstance.created_by == user_id)
            filters2.append(CloudServerInstance.created_by == user_id)

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        return sum(x[0] for x in bare + cloud)

    # 纳管，内存
    def total_memory(self, user_id: Optional[int], isAll: bool = False):
        query1 = self.db.query(BareMetalInstance.system_disk_size)
        query2 = self.db.query(CloudServerInstance.system_disk_size)

        filters1 = [BareMetalInstance.system_disk_size > 0]
        filters2 = [CloudServerInstance.system_disk_size > 0]
        if user_id is not None:
            filters1.append(BareMetalInstance.created_by == user_id)
            filters2.append(CloudServerInstance.created_by == user_id)

        if isAll:
            filters1.append(BareMetalInstance.is_released == 0)
            filters2.append(CloudServerInstance.is_released == 0)

        bare = query1.filter(*filters1).all()
        cloud = query2.filter(*filters2).all()

        return sum(x[0] for x in bare + cloud)

    # 纳管，存储
    def total_storage(self, user_id: Optional[int], isAll: bool = False):
        query1 = self.db.query(CbsDisk.disk_size)

        filters1 = [CbsDisk.disk_size > 0]
        if user_id is not None:
            filters1.append(CbsDisk.created_by == user_id)

        if isAll:
            filters1.append(CbsDisk.is_released == 0)

        cbs = query1.filter(*filters1).all()

        return sum(x[0] for x in cbs)

    # 纳管gpu分配率
    def current_gpu_rate_by_provider(self, user_id: Optional[int]):
        # 运行中的 GPU
        running_bare_query = (
            self.db.query(
                BareMetalInstance.cloud_provider_code,
                func.sum(BareMetalInstance.gpu_amount)
            )
            .filter(
                BareMetalInstance.is_released == 0,
                BareMetalInstance.status == 'RUNNING',
                BareMetalInstance.gpu_amount > 0
            )
        )
        if user_id is not None:
            running_bare_query = running_bare_query.filter(BareMetalInstance.created_by == user_id)
        running_bare = running_bare_query.group_by(BareMetalInstance.cloud_provider_code).all()
        # 纳管中的 GPU 总量
        total_bare_query = (
            self.db.query(
                BareMetalInstance.cloud_provider_code,
                func.sum(BareMetalInstance.gpu_amount)
            )
            .filter(
                BareMetalInstance.is_released == 0,
                BareMetalInstance.gpu_amount > 0
            )
        )
        if user_id is not None:
            total_bare_query = total_bare_query.filter(BareMetalInstance.created_by == user_id)
        total_bare = total_bare_query.group_by(BareMetalInstance.cloud_provider_code).all()


        running_cloud_query = (
            self.db.query(
                CloudServerInstance.cloud_provider_code,
                func.sum(CloudServerInstance.gpu_amount)
            )
            .filter(
                CloudServerInstance.is_released == 0,
                CloudServerInstance.status == 'RUNNING',
                CloudServerInstance.gpu_amount > 0
            )
        )
        if user_id is not None:
            running_cloud_query = running_cloud_query.filter(CloudServerInstance.created_by == user_id)
        running_cloud = running_cloud_query.group_by(CloudServerInstance.cloud_provider_code).all()



        total_cloud_query = (
            self.db.query(
                CloudServerInstance.cloud_provider_code,
                func.sum(CloudServerInstance.gpu_amount)
            )
            .filter(
                CloudServerInstance.is_released == 0,
                CloudServerInstance.gpu_amount > 0
            )
        )
        if user_id is not None:
            total_cloud_query = total_cloud_query.filter(CloudServerInstance.created_by == user_id)
        total_cloud = total_cloud_query.group_by(CloudServerInstance.cloud_provider_code).all()

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
    def sum_monthly_spent(self, user_id: Optional[int], year: int, month: int) -> float:
        query = self.db.query(func.sum(FundsFlow.amount)).filter(
            FundsFlow.direction == 'OUT',
            FundsFlow.flow_type == 'PAY_ORDER',
            extract('year', FundsFlow.created_at) == year,
            extract('month', FundsFlow.created_at) == month
        )
        if user_id is not None:
            query = query.filter(FundsFlow.created_by == user_id)
        total = query.scalar()
        return float(total or 0)

    # 当月收入
    def sum_monthly_income(self, user_id: Optional[int], year: int, month: int) -> float:
        query = self.db.query(func.sum(FundsFlow.amount)).filter(
            FundsFlow.direction == 'IN',
            extract('year', FundsFlow.created_at) == year,
            extract('month', FundsFlow.created_at) == month
        )
        if user_id is not None:
            query = query.filter(FundsFlow.created_by == user_id)
        total = query.scalar()

        return float(total or 0)

    # 可开发票金额
    def sum_monthly_invoice_amount(self, user_id: Optional[int], billing_period: Optional[str]=None) -> float:
        query = self.db.query(func.sum(InvoiceItem.invoice_amount)) \
            .filter(
            InvoiceItem.status == 'UNISSUED'
        )
        if user_id is not None:
            query = query.filter(InvoiceItem.created_by == user_id)
        if billing_period:
            query = query.filter(
                InvoiceItem.billing_period == billing_period
            )

        total = query.scalar()
        return float(total or 0)

    # 已开票金额
    def sum_monthly_invoiced_amount(
        self,
        user_id: Optional[int],
        billing_period: Optional[str]=None
    ) -> float:
        query = self.db.query(func.sum(InvoiceRecord.amount)) \
            .filter(
            InvoiceRecord.status == 'ISSUED'
        )
        if user_id is not None:
            query = query.filter(InvoiceRecord.created_by == user_id)

        if billing_period:
            query = query.filter(
                InvoiceItem.billing_period == billing_period
            )
        total = query.scalar()
        return float(total or 0)

    # 抵佣金
    def sum_monthly_credit(self, user_id: Optional[int], year: int, month: int) -> float:
        query = self.db.query(func.sum(OrderDetail.credit_amount)) \
            .join(Order, OrderDetail.order_id == Order.id) \
            .filter(
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        )
        if user_id is not None:
            query = query.filter(Order.created_by == user_id)
        total = query.scalar()
        return float(total or 0)

    # 代金券
    def sum_monthly_voucher(self, user_id: Optional[int], year: int, month: int) -> float:
        query = self.db.query(func.sum(OrderDetail.voucher_amount)) \
            .join(Order, OrderDetail.order_id == Order.id) \
            .filter(
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        )
        if user_id is not None:
            query = query.filter(Order.created_by == user_id)
        total = query.scalar()
        return float(total or 0)

    # 账户可用金额
    def get_available_quota(self, user_id: Optional[int]) -> float:
        query = self.db.query(func.sum(Account.balance))
        if user_id is not None:
            query = query.filter(Account.created_by == user_id)
        # if year and month:
        #     return query.filter(
        #         extract('year', FundsFlow.created_at) == year,
        #         extract('month', FundsFlow.created_at) == month
        #     ).scalar()

        result = query.scalar()
        return float(result or 0)

    # 当月订单数
    def count_monthly_orders(self, user_id: Optional[int], year: int, month: int) -> int:
        query = self.db.query(func.count(Order.id)) \
            .filter(
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        )
        if user_id is not None:
            query = query.filter(Order.created_by == user_id)
        total = query.scalar()

        return int(total or 0)

    """
    field_name: 'cloud_provider_code' / 'product_name' / 'business_name'
    """
    def top5_by_field(self, user_id: Optional[int], year: int, month: int, field_name: str):
        # 总金额
        total_query = self.db.query(func.sum(Order.amount_payable)) \
                           .filter(
            Order.pay_status == 'SUCCESS',
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        )
        if user_id is not None:
            total_query = total_query.filter(Order.created_by == user_id)
        total_amount = total_query.scalar() or 0

        if total_amount == 0:
            return []

        # 每个名称的金额汇总
        rows_query = self.db.query(
            getattr(Order, field_name).label("name"),
            func.sum(Order.amount_payable).label("amount")
        ) \
            .filter(
            Order.pay_status == 'SUCCESS',
            extract('year', Order.created_at) == year,
            extract('month', Order.created_at) == month
        )
        if user_id is not None:
            rows_query = rows_query.filter(Order.created_by == user_id)
        rows = rows_query \
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
        system: int = 1,
    ):
        query = self.db.query(AuditLog).filter(
            AuditLog.created_by == user_id,
            AuditLog.is_read.is_(False),
            AuditLog.system == system,
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
    def count_unread_notifications(self, user_id: int, system: int = 1) -> int:
        return (
            self.db.query(func.count(AuditLog.id))
            .filter(
                AuditLog.created_by == user_id,
                AuditLog.is_read.is_(False),
                AuditLog.system == system,
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

    # 总收入趋势（充值）
    def income_trend(
        self,
        *,
        user_id: int,
        start_at: datetime,
        end_at: datetime,
        granularity: str,
    ):
        fmt_map = {
            "hour": "%Y-%m-%d %H:00:00",
            "day": "%Y-%m-%d",
            "month": "%Y-%m",
        }
        fmt = fmt_map[granularity]
        bucket = func.date_format(FundsFlow.created_at, fmt).label("bucket")

        rows = (
            self.db.query(bucket, func.sum(FundsFlow.amount).label("total"))
            .filter(
                FundsFlow.created_by == user_id,
                FundsFlow.direction == Direction.IN,
                FundsFlow.flow_type == FlowType.RECHARGE,
                FundsFlow.created_at >= start_at,
                FundsFlow.created_at <= end_at,
            )
            .group_by(bucket)
            .order_by(bucket.asc())
            .all()
        )

        return {r.bucket: float(r.total or 0) for r in rows}
