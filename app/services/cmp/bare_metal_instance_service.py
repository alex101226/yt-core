from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from nanoid import generate

from app.common.util import gen_random_name
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger
from app.common.ipaddress import allocate_private_ip
from app.core.security import hash_password

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.subnet_service import SubnetService
from app.services.cmp.vpc_service import VPCService
from app.services.cmp.eip_service import EIPService

from app.services.cmp.cbs_service import CbsService
# 通知
from app.services.cmp.operation_helper import execute_with_notification

from app.repositories.cmp.bare_metal_instance_repo import BareMetalInstanceRepo
from app.schemas.cmp.bare_metal_instance_schema import (
BareMetalInstanceCreate, BareMetalInstanceOut, BareMetalInstancePage
)

class BareMetalInstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BareMetalInstanceRepo(db)
        self.cbs_service = CbsService(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.eip_service = EIPService(db)
        self.vpc_service = VPCService(db)
        self.subnet_service = SubnetService(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)


    # 创建裸金属
    def bare_metal_instance_create(self, user: dict, data: BareMetalInstanceCreate):
        user_id = user.get('user_id')
        def _do():
            try:
                with self.db.begin():
                    # 先查子网
                    subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
                    private_ips = {row.private_ip for row in subnet_all}

                    # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
                    cidr = data.cidr_block
                    private_ip = ''
                    if cidr:
                        # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
                        private_ip = allocate_private_ip(cidr, private_ips)

                    # 1️⃣ 构造主表数据
                    payload = {
                        **data.model_dump(),
                        "hashed_password": hash_password(data.password),
                        "status": "RUNNING",
                        "delivery_status": "DELIVERED",
                        "last_operation": "RUNNING",
                        "instance_id": f"bare_metal-{generate(size=12)}",
                        "created_by": user_id,
                        "private_ip": private_ip,
                        "physical_machine_id": f"bare_metal-physical-{generate(size=6)}",
                    }
                    payload.pop("cidr_block", None)
                    payload.pop("password", None)

                    instance = self.repo.bare_metal_create(payload)

                    if not instance:
                        raise BusinessException(code=ErrorCode.FAILED, message="实例创建失败")  # 不返回 False，直接抛异常

                    # 查看账户
                    account = self.account_service.account_exists(user_id)
                    if not account:
                        raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

                    # 创建成功，生成周期性任务
                    self.bill_service.create(
                        user_id=user_id,
                        account_id=account.id,
                        resource_type="BAREMETAL",
                        charge_type=instance.instance_charge_type,
                        instance_id=instance.instance_id,
                        instance=instance,
                        unit_price=data.price,  # 👈 创建时提交的价格
                    )

                    #  设置vpc
                    self.vpc_service.update_vpc(data.vpc_id)

                    # 设置子网
                    self.subnet_service.update_subnet(data.vswitch_id)

                    # 5. 是否需要公网 IP
                    public_ip = self.eip_service.allocate_eip(
                        provider_code=data.cloud_provider_code,
                        region_id=data.region_id,
                        instance_id=instance.id,
                    )

                    instance.public_ip = public_ip

                    # -----------------------------
                    # 2. 创建系统盘 CBS
                    # -----------------------------
                    system_disk_data = {
                        "cloud_provider_code": data.cloud_provider_code,
                        "region_id": data.region_id,
                        "zone_id": data.zone_id,
                        "resource_group_id": data.resource_group_id,
                        "disk_name": gen_random_name('cbs'),
                        "disk_type": "system",  # 磁盘类型：system 系统盘 / data 数据盘。
                        "disk_category": data.system_disk_category,  # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
                        "disk_size": data.system_disk_size,  # 磁盘大小
                        "charge_type": data.instance_charge_type,  # 计费方式：PrePaid 包年包月 / PostPaid 按量付费
                        "period": data.period or 1,  # 包年月的月份
                        "auto_renew": data.auto_renew,
                        "attached_instance_id": str(instance.id),  # 挂载的实例 ID（ecs/lh/lb）
                        "attached_device": data.instance_name,  # 挂载点名称，如 /dev/vdb
                        "attached_time": datetime.now(timezone.utc),  # 挂载时间
                        "description": f"系统盘，挂载到实例 {instance.instance_name}",
                        "tags": []
                    }
                    self.cbs_service.cbs_create_auto(user, system_disk_data, instance.instance_charge_type, 2.5)

                    #   绑定资源组
                    self.resource_bind_service.bind(
                        ResourceGroupBindingCreate(
                            cloud_provider_code=data.cloud_provider_code,
                            user_id=user_id,
                            resource_group_id=data.resource_group_id,
                            resource_type="bare-metal",
                            resource_id=str(instance.id),
                        )
                    )
                return instance
            except BusinessException as exception:
                self.db.rollback()
                raise exception

        # -------- 交给统一封装处理通知 --------
        return execute_with_notification(
            db=self.db,
            user=user,
            system=1,
            system_name="算力调度",
            action_mode="BAREMETAL",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else None,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="裸金属创建成功",
            failed_desc="裸金属创建失败",
            func=_do
        )


    # 分页列表
    def bare_metal_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        instance_name: Optional[str] = None,
        instance_type_id: Optional[str] = None,
        public_ip: Optional[str] = None,
        status: Optional[str] = None,
        ssh_proxy_port: Optional[int] = None,
    ):
        items, total = self.repo.bare_metal_page_list(
            user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id,
            instance_id, instance_name, instance_type_id, public_ip, status, ssh_proxy_port
        )

        return BareMetalInstancePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[BareMetalInstanceOut.model_validate(item) for item in items]
        )

