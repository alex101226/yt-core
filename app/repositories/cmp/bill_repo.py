from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants.billing_meta import BILLING_META_MAP
from app.constants.enums import BillingStatus, ResourceType
from app.core.logger import logger
from app.models.cmp import (
CloudServerInstance, BareMetalInstance, GPFSFile, CbsDisk,
LoadBalancerACL, Eip, K8sCluster, CephfsFile
)

from app.models.cmp.billing_instance import BillingInstance, BillingMethod
from app.models.cmp.account_funds_flow import FundsFlow
from app.models.cmp.order import Order
from app.models.cmp.order_detail import OrderDetail

class BillRepository:
    def __init__(self, db: Session):
        self.db = db

    # 账单流水
    def get_billing_flows(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        billing_id: int = None,
        start_month: str = None,  # "YYYY-MM"
        end_month: str = None,  # "YYYY-MM"
        consume_type: str = None,
        billing_type: str = None,
        cloud_provider_code: str = None,
        billing_status: str = None,  # '已结算' / '未结算'
    ):
        offset = (page - 1) * page_size

        query = (
            self.db.query(
                Order.product_name,
                Order.business_name,
                Order.consume_type,  # 消费类型：VOLUME_BASED=按量计费/PACKAGE_MONTHLY=包年月计费
                Order.pay_status,
                Order.amount_payable,
                Order.settlement_type,
                Order.cloud_provider_code,
                Order.charge_mode,
                OrderDetail.billing_period,
                OrderDetail.coupon_amount,
                OrderDetail.unit_price,
                OrderDetail.balance_amount,
                OrderDetail.credit_amount,
                OrderDetail.voucher_amount,
                OrderDetail.owe_amount,
                FundsFlow.id,
                FundsFlow.flow_no,
                FundsFlow.created_at.label("consume_time"),
                FundsFlow.ref_type,  # 订单类型：充值订单, 预付费场景,后付费 / 按量计费,退订/冲正    流水类型：RECHARGE/PAY_ORDER/REFUND等
            )
            .select_from(FundsFlow)
            .join(
                Order,
                (FundsFlow.ref_type == "PRODUCT_ORDER") &
                (FundsFlow.ref_id == Order.id)
            )
            .outerjoin(OrderDetail, OrderDetail.order_id == Order.id)
        )
        filters = [Order.created_by == user_id]
        # 可选查询条件
        if billing_id:
            filters.append(FundsFlow.flow_no == billing_id)
        if start_month and end_month:
            # billing_period_str = billing_period.strftime("%Y-%m")
            filters.append(
                OrderDetail.billing_period.between(start_month, end_month)
            )
        if consume_type:
            filters.append(Order.consume_type == consume_type)
        if billing_type:
            filters.append(FundsFlow.flow_type == billing_type)
        if cloud_provider_code:
            filters.append(Order.cloud_provider_code == cloud_provider_code)
        if billing_status:
            if billing_status == "已结算":
                filters.append(Order.pay_status == "SUCCESS")
            elif billing_status == "未结算":
                filters.append(Order.pay_status != "SUCCESS")

        if filters:
            query = query.filter(*filters)

        total = query.count()
        items = query.order_by(FundsFlow.id.desc()) \
            .offset(offset).limit(page_size) \
            .all()
        # 转换账单状态
        items_dict = [
            {
                "flow_no": row.flow_no,
                "consume_time": row.consume_time,
                "ref_type": row.ref_type,
                "charge_mode": row.charge_mode,
                "product_name": row.product_name,
                "business_name": row.business_name,
                "consume_type": row.consume_type,
                "pay_status": row.pay_status,
                "amount_payable": row.amount_payable,
                "settlement_type": row.settlement_type,
                "cloud_provider_code": row.cloud_provider_code,
                "billing_period": row.billing_period,
                "coupon_amount": row.coupon_amount,
                "unit_price": row.unit_price,
                "balance_amount": row.balance_amount,
                "credit_amount": row.credit_amount,
                "voucher_amount": row.voucher_amount,
                "owe_amount": row.owe_amount,
                "billing_status": "已结算" if row.pay_status == "SUCCESS" else "未结算"
            }
            for row in items
        ]
        logger.info(f'看下结果 {items_dict}')
        return items_dict, total

    # 收支明细
    def fund_detail_page_lis(
        self,
        user_id: int,
        page: int,
        page_size: int,
        flow_no: Optional[str] = None,
        third_trade_no: Optional[str] = None,
        direction: Optional[str] = None,
        flow_type: Optional[str] = None,
        channel: Optional[str] = None,
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
    ):
        query = self.db.query(FundsFlow)
        filters = [FundsFlow.created_by == user_id]

        if flow_no:
            filters.append(FundsFlow.flow_no.like(f'%{flow_no}%'))
        if third_trade_no:
            filters.append(FundsFlow.third_trade_no.like(f'%{third_trade_no}%'))

        if direction:
            filters.append(FundsFlow.direction==direction)
        if flow_type:
            filters.append(FundsFlow.flow_type==flow_type)
        if channel:
            filters.append(FundsFlow.channel==channel)

        if start_at and end_at:
            filters.append(
                FundsFlow.created_at.between(start_at, end_at)
            )

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(FundsFlow.id.desc()).offset(offset_value).limit(page_size).all()
        out_items = [
            {
                "id": row.id,
                "flow_no": row.flow_no,
                "direction": row.direction,
                "flow_type": row.flow_type,
                "fund_type": row.fund_type,
                "amount": row.amount,
                "balance_after": row.balance_after,
                "ref_type": row.ref_type,
                "ref_id": row.ref_id,
                "billing_period": row.billing_period,
                "channel": row.channel,
                "third_trade_no": row.third_trade_no,
                "description": row.description,
                "created_at": row.created_at,
            } for row in items
        ]
        return out_items, total

    # 月收支汇总
    def monthly_fund_summary(
        self,
        user_id: int,
        page: int,
        page_size: int,
        start_month: str,  # "YYYY-MM"
        end_month: str,  # "YYYY-MM"
        direction: Optional[str] = None,
        flow_type: Optional[str] = None,
        channel: Optional[str] = None,
        flow_no: Optional[str] = None,
        # third_trade_no: Optional[str] = None,
    ):
        query = self.db.query(
            FundsFlow.billing_period.label("month"),
            FundsFlow.direction,
            FundsFlow.flow_type,
            FundsFlow.channel,
            FundsFlow.fund_type,
            func.sum(FundsFlow.amount).label("total_amount"),
        ).filter(
            FundsFlow.created_by == user_id,
            FundsFlow.billing_period.between(start_month, end_month)
        )

        # 可选条件
        if direction:
            query = query.filter(FundsFlow.direction == direction)
        if flow_type:
            query = query.filter(FundsFlow.flow_type == flow_type)
        if channel:
            query = query.filter(FundsFlow.channel == channel)
        if flow_no:
            query = query.filter(FundsFlow.flow_no.like(f"%{flow_no}%"))
        # if third_trade_no:
        #     query = query.filter(FundsFlow.third_trade_no.like(f"%{third_trade_no}%"))

        # 分组
        query = query.group_by(
            FundsFlow.billing_period,
            FundsFlow.direction,
            FundsFlow.flow_type,
            FundsFlow.channel,
            FundsFlow.fund_type
        )

        # 分页
        total = query.count()  # 分组后的总条数
        offset_value = (page - 1) * page_size
        items = query.order_by("month").offset(offset_value).limit(page_size).all()

        out_items = [
            {
                "month": row.month,
                "direction": row.direction,
                "flow_type": row.flow_type,
                "channel": row.channel,
                "fund_type": row.fund_type,
                "total_amount": row.total_amount,
            }
            for row in items
        ]
        return out_items, total


    # 周期计费任务创建
    def bill_create(self, instance: BillingInstance):
        self.db.add(instance)
        self.db.flush()
        self.db.refresh(instance)  # ✅ 确保 instance.id 可用
        return instance

    # 周期计费任务修改
    def bill_update(self, billing_id: int, *, last_time: Optional[datetime], next_time: Optional[datetime], status):
        find = self.bill_by_id_find(billing_id)
        if not find:
          return None
        find.last_billing_time = last_time
        find.next_bill_time = next_time
        find.status=status
        # self.db.commit()
        self.db.flush()
        return find

    # 查询单条的计费任务
    def bill_by_id_find(self, bill_id: int):
        return self.db.query(BillingInstance).filter(BillingInstance.id == bill_id).first()


    def find_due_billings(self, now: datetime):
        return (
            self.db.query(BillingInstance)
            .filter(
                BillingInstance.status == BillingStatus.ACTIVE,
                BillingInstance.next_bill_time <= now
            )
            .with_for_update()  # 防并发重复扣费
            .all()
        )

    # 查询计费单条的资源id
    def bill_by_resource_id(self, resource_id):
        return self.db.query(BillingInstance).filter(BillingInstance.resource_id == resource_id).first()

    # 根据任务id查询
    def get_by_id(self, task_id: int):
        return self.db.query(BillingInstance).filter(BillingInstance.id == task_id).first()

    # 退订列表
    def unsubscribe_page_list(self, parent_id: int, page: int, page_size: int):
        unsubscribe = [
            ResourceType.SERVER,
            ResourceType.BAREMETAL,
            ResourceType.CLUSTER,
            ResourceType.GPFS,
            ResourceType.CEPHFS,
            ResourceType.DISK,
            ResourceType.EIP,
            ResourceType.LOAD_INSTANCE
        ]

        query = self.db.query(BillingInstance) \
            .filter(
            BillingInstance.resource_type.in_(unsubscribe),
            BillingInstance.status.in_([
                BillingStatus.CREATED,
                BillingStatus.ACTIVE,
                BillingStatus.SUSPENDED,
            ]),
            BillingInstance.created_by == parent_id,
            BillingInstance.is_released == 0,
        )

        total = query.count()

        # 分页
        tasks = query.offset((page - 1) * page_size).limit(page_size).all()

        result_list = []
        for t in tasks:
            # 2️⃣ 查资源详情
            resource = self.fetch_resource(t.resource_type, t.resource_id)
            if not resource:
                continue
            meta = BILLING_META_MAP[ResourceType(t.resource_type)]
            result_list.append({
                "task_id": t.id,
                "product_name": meta.product_name,  # 商品
                "instance_name": self.get_resource_display_name(t.resource_type, resource),  # 实例名称
                "resource_id": self.get_resource_business_id(t.resource_type, resource) or t.resource_id,  # 实例ID
                "config_info": self.get_resource_config(resource),  # 配置信息
                "cloud_provider": t.cloud_provider_code,  # 云厂商
                "region_id": getattr(resource, 'region_id', ''),  # 区域
                "zone_id": getattr(resource, 'zone_id', ''),  # 可用区
                "created_at": getattr(resource, 'created_at', None),  # 实例创建时间
                "billing_end_time": getattr(t, 'billing_end_time', None),  # 实例到期时间
                "action": "unsubscribe"  # 操作
            })
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": result_list
        }

    def fetch_resource(self, resource_type: str, resource_id: int):
        # 根据资源类型去对应表查
        mapping = {
            ResourceType.SERVER: CloudServerInstance,
            ResourceType.BAREMETAL: BareMetalInstance,
            ResourceType.CLUSTER: K8sCluster,
            ResourceType.GPFS: GPFSFile,
            ResourceType.CEPHFS: CephfsFile,
            ResourceType.DISK: CbsDisk,
            ResourceType.EIP: Eip,
            ResourceType.LOAD_INSTANCE: LoadBalancerACL,  # 假设有
        }
        model = mapping.get(resource_type)
        if not model:
            return None
        return self.db.query(model).filter(model.id == resource_id).first()

    def get_resource_display_name(self, resource_type: str, resource) -> str:
        attr_map = {
            ResourceType.SERVER: "instance_name",
            ResourceType.BAREMETAL: "instance_name",
            ResourceType.CLUSTER: "cluster_name",
            ResourceType.GPFS: "fs_name",
            ResourceType.CEPHFS: "fs_name",
            ResourceType.DISK: "disk_name",
            ResourceType.EIP: "public_ip",
            ResourceType.LOAD_INSTANCE: "name",
        }
        attr_name = attr_map.get(resource_type)
        return getattr(resource, attr_name, "") if attr_name else ""

    def get_resource_business_id(self, resource_type: str, resource):
        attr_map = {
            ResourceType.SERVER: "instance_id",
            ResourceType.BAREMETAL: "instance_id",
            ResourceType.CLUSTER: "cluster_id",
            ResourceType.GPFS: "fs_id",
            ResourceType.CEPHFS: "fs_id",
            ResourceType.DISK: "disk_id",
            ResourceType.EIP: "eip_id",
            ResourceType.LOAD_INSTANCE: "lb_id",
        }
        attr_name = attr_map.get(resource_type)
        return getattr(resource, attr_name, None) if attr_name else None

    def fetch_resource_by_business_id(self, resource_identifier: str):
        mapping = {
            ResourceType.SERVER: (CloudServerInstance, "instance_id"),
            ResourceType.BAREMETAL: (BareMetalInstance, "instance_id"),
            ResourceType.CLUSTER: (K8sCluster, "cluster_id"),
            ResourceType.GPFS: (GPFSFile, "fs_id"),
            ResourceType.CEPHFS: (CephfsFile, "fs_id"),
            ResourceType.DISK: (CbsDisk, "disk_id"),
            ResourceType.EIP: (Eip, "eip_id"),
            ResourceType.LOAD_INSTANCE: (LoadBalancerACL, "lb_id"),
        }
        for resource_type, (model, field_name) in mapping.items():
            resource = self.db.query(model).filter(getattr(model, field_name) == resource_identifier).first()
            if resource:
                return resource_type, resource
        return None, None

    def get_resource_config(self, resource) -> str:
        # 统一组装配置描述，例如 CPU/内存/磁盘/带宽等
        info = []
        if hasattr(resource, 'cpu') and hasattr(resource, 'gpu_memory'):
            info.append(f"CPU:{resource.cpu} 核")
            info.append(f"GPU:{resource.gpu_memory} GB")
        if hasattr(resource, 'system_disk_size'):
            info.append(f"{resource.system_disk_size} GB")
        if hasattr(resource, 'disk_size'):
            info.append(f"{resource.disk_size} GB")
        if hasattr(resource, 'bandwidth'):
            info.append(f"{resource.bandwidth} Mbps")
        return ', '.join(info)

    # 'CREATED','ACTIVE','SUSPENDED','RELEASED'
    # 执行退订
    def set_unsubscribe(self, task_id):
        find = self.get_by_id(int(task_id)) if str(task_id).isdigit() else None
        if not find:
            resource_type, resource = self.fetch_resource_by_business_id(str(task_id))
            if resource_type and resource:
                find = (
                    self.db.query(BillingInstance)
                    .filter(
                        BillingInstance.resource_type == resource_type,
                        BillingInstance.resource_id == resource.id,
                        BillingInstance.is_released == 0,
                        BillingInstance.status.in_([
                            BillingStatus.CREATED,
                            BillingStatus.ACTIVE,
                            BillingStatus.SUSPENDED,
                        ]),
                    )
                    .order_by(BillingInstance.id.desc())
                    .first()
                )
        if not find:
            return None
        now = datetime.now(timezone.utc)
        if find.billing_method == BillingMethod.PrePaid:
            find.auto_renew = False
            if not find.billing_end_time:
                last_billing = find.last_billing_time or find.billing_start_time or now
                find.billing_end_time = last_billing
        else:
            find.billing_end_time = find.next_bill_time or now
        self.db.commit()
        self.db.refresh(find)
        return find

    # 欠费暂停：按用户维度停止计费任务
    def suspend_by_user(self, user_id: int):
        updated = (
            self.db.query(BillingInstance)
            .filter(
                BillingInstance.created_by == user_id,
                BillingInstance.is_released == 0,
                BillingInstance.status.in_([BillingStatus.ACTIVE, BillingStatus.CREATED]),
            )
            .update(
                {BillingInstance.status: BillingStatus.SUSPENDED},
                synchronize_session=False
            )
        )
        return updated

    # 欠费恢复：按用户维度恢复计费任务
    def resume_by_user(self, user_id: int):
        updated = (
            self.db.query(BillingInstance)
            .filter(
                BillingInstance.created_by == user_id,
                BillingInstance.is_released == 0,
                BillingInstance.status == BillingStatus.SUSPENDED,
            )
            .update(
                {BillingInstance.status: BillingStatus.ACTIVE},
                synchronize_session=False
            )
        )
        return updated
