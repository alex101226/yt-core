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
from app.core.security import hash_password, encrypt_text, decrypt_text

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
BareMetalInstanceCreate, BareMetalInstanceOut, BareMetalInstancePage,
BareActionSchema, BareUpdatePassword, BareUpdateCharge
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

    # 创建裸金属执行
    def _create_instance_internal(self, user: dict, data: BareMetalInstanceCreate):
        user_id = user['user_id']
        username = user['username']

        # 先查子网
        subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
        private_ips = {row.private_ip for row in subnet_all}

        # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
        cidr = self.subnet_service.subnet_by_id(data.vswitch_id)
        # cidr = data.cidr_block
        private_ip = ''
        if cidr:
            # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
            private_ip = allocate_private_ip(cidr.cidr_block, private_ips)

        # 1️⃣ 构造主表数据
        payload = {
            **data.model_dump(),
            "hashed_password": encrypt_text(data.password),
            "status": "RUNNING",
            "delivery_status": "DELIVERED",
            "instance_id": f"bare_metal-{generate(size=12)}",
            "created_by": user_id,
            "created_by_name": username,
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
            user=user,
            account_id=account.id,
            resource_type="BAREMETAL",
            charge_type=instance.charge_type,
            instance_id=instance.instance_id,
            instance=instance,
            unit_price=data.price,  # 👈 创建时提交的价格
        )

        #  设置vpc
        self.vpc_service.update_vpc(data.vpc_id, 'bind')

        # 设置子网
        self.subnet_service.update_subnet(data.vswitch_id, 'bind')

        # 5. 是否需要公网 IP  绑定实例类型，如 ecs/bms/lb
        public_ip = self.eip_service.allocate_eip(
            provider_code=data.cloud_provider_code,
            region_id=data.region_id,
            instance_id=instance.id,
            bind_instance_type='baremetal'
        )

        instance.public_ip = public_ip

        # -----------------------------
        # 2. 创建系统盘 CBS
        # -----------------------------
        system_disk_data = {
            "disk_name": gen_random_name('cbs'),
            "disk_type": "system",  # 磁盘类型：system 系统盘 / data 数据盘。
            "disk_category": data.system_disk_category,  # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
            "disk_size": data.system_disk_size,  # 磁盘大小
            "attached_instance_id": str(instance.id),  # 挂载的实例 ID（ecs/lh/lb）
            "attached_device": 'baremetal',  # 挂载点名称
            "attached_time": datetime.now(timezone.utc),  # 挂载时间
            "is_attached": bool(instance.id),
            "description": f"系统盘，挂载到实例 {instance.instance_name}",
        }
        self.cbs_service.cbs_create_auto(user, 2.5, system_disk_data, instance)

        #   绑定资源组
        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                created_by=user_id,
                created_by_name=username,
                resource_group_id=data.resource_group_id,
                resource_type="bare-metal",
                resource_id=str(instance.id),
            )
        )
        return instance

    # 创建裸金属
    def bare_metal_instance_create(self, user: dict, data: BareMetalInstanceCreate):
        def _do():
            try:
                with self.db.begin():
                    return self._create_instance_internal(user, data)

            except BusinessException as exception:
                # self.db.rollback()
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
        parent_id: int,
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
            parent_id, page, page_size, provider_code, region_id, zone_id, resource_group_id,
            instance_id, instance_name, instance_type_id, public_ip, status, ssh_proxy_port
        )

        return BareMetalInstancePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[BareMetalInstanceOut.model_validate(item) for item in items]
        )

    # 开机，关机，重启，
    def start_instance(self, data: BareActionSchema):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        instance.status = data.status
        instance.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(instance)
        return {"instance_id": instance.instance_id}

    # 修改服务器密码   hash_password
    def save_server_password(self, data: BareUpdatePassword):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        hashed_password = encrypt_text(data.password)
        result = self.repo.save_server_password(instance.instance_id, hashed_password)
        return result

    # 克隆
    def server_clone(self, user: dict, instance_id: int):
        # 事务 + 日志
        with self.db.begin():
            db_instance = self.repo.get_instance_by_find(instance_id)
            if not db_instance:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

            bill_find = self.bill_service.bill_by_resource_id(db_instance.id)

            payload = BareMetalInstanceCreate(
                instance_name=f'{db_instance.instance_name}_copy',
                description=db_instance.description,
                cloud_provider_code=db_instance.cloud_provider_code,
                region_id=db_instance.region_id,
                zone_id=db_instance.zone_id,
                resource_group_id=db_instance.resource_group_id,
                instance_type=db_instance.instance_type,
                instance_type_id=db_instance.instance_type_id,
                image_id=db_instance.image_id,
                cpu=db_instance.cpu,
                gpu_memory=db_instance.gpu_memory,
                gpu_amount=db_instance.gpu_amount,
                gpu_spec=db_instance.gpu_spec,
                system_disk_category=db_instance.system_disk_category,
                system_disk_size=db_instance.system_disk_size,
                quantity=db_instance.quantity,
                charge_type=db_instance.charge_type,
                period=db_instance.period,
                auto_renew=db_instance.auto_renew,
                vpc_id=db_instance.vpc_id,
                vswitch_id=db_instance.vswitch_id,
                security_group_id=db_instance.security_group_id,
                os_type=db_instance.os_type,
                architecture=db_instance.architecture,
                hostname=db_instance.hostname,
                price=bill_find.unit_price,
                password='123456',
                enable_ssh_agent=db_instance.enable_ssh_agent,
                install_gpu_driver=db_instance.install_gpu_driver,
            )
            return self._create_instance_internal(user, payload)


    # 转包年月  实例计费类型:PrePaid（包年包月）/PostPaid（按量付费）
    def save_charge_type(self, data: BareUpdateCharge):
        result = self.repo.save_charge_type(data.model_dump())
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return result

    # 查看服务器密码
    def view_password(self, instance_id: int):
        instance = self.repo.get_instance_by_find(instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        password = decrypt_text(instance.hashed_password)
        return password

    # 开启/关闭释放保护
    def toggle_server_release(self, instance_id: int, user_id: int):
        find = self.repo.toggle_server_release(instance_id)
        if not find:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return find

    # 开启，关闭ssh代理
    def server_ssh(self, instance_id: int):
        result = self.repo.toggle_server_ssh(instance_id)
        if not result:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return result

    # 释放
    def server_release(self, instance_id: int):
        with self.db.begin():
            instance = self.repo.get_instance_by_find(instance_id)
            if not instance:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

            if instance.enable_protection == 1:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="此服务器无法释放")

            active_status = {
                'INIT',
                'PREPARE_CREATE',
                'STARTING',
                'CREATING',
                'RUNNING',
                'DEPLOYING',
                'DISK_EXPANDING',
                'PREPARE_REBOOT',
                'RELEASED',
                'STOPPING',
                'PREPARE_START',
                'START_FAILED',
                'REBOOT_FAILED',
                'RELEASING'
            }

            if instance.status in active_status:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前服务器正在使用，无法释放")

            result = self.repo.server_release(instance_id)
            if not result:
                raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
            #  设置vpc
            self.vpc_service.update_vpc(instance.vpc_id, 'release')

            # 设置子网
            self.subnet_service.update_subnet(instance.vswitch_id, 'release')
            return result