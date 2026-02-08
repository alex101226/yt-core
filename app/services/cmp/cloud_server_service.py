# app/services/cmp/instance_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.common.util import gen_random_name
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.common.ipaddress import allocate_private_ip
from app.core.security import encrypt_text, decrypt_text

from app.services.cmp.bill_service import BillService
from app.services.cmp.account_service import AccountService

from app.services.cmp.subnet_service import SubnetService
from app.services.cmp.vpc_service import VPCService
from app.services.cmp.eip_service import EIPService

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.cbs_service import CbsService

# 通知
from app.services.cmp.operation_helper import execute_with_notification

from app.repositories.cmp.cloud_server_instance_repo import ServerInstanceRepo
from app.schemas.cmp.cloud_server_instance_schema import (
InstanceActionSchema, InstanceUpdatePassword, InstanceCreateSchema, InstanceBaseOut, InstancePage,
InstanceUpdateCharge, InstanceUpdateImage
)

class InstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServerInstanceRepo(db)
        self.cbs_service = CbsService(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.eip_service = EIPService(db)
        self.vpc_service = VPCService(db)
        self.subnet_service = SubnetService(db)
        self.account_service = AccountService(db)
        self.bill_service = BillService(db)

    # =========================
    # 核心创建逻辑，不管事务
    # =========================
    def _create_instance_internal(self, user: dict, data: InstanceCreateSchema):
        user_id = user['user_id']
        username = user['username']

        # -----------------------------
        # 1. 处理私网 IP
        # -----------------------------
        subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
        private_ips = {row.private_ip for row in subnet_all}

        cidr = self.subnet_service.subnet_by_id(data.vswitch_id)
        private_ip = ''
        if cidr:
            private_ip = allocate_private_ip(cidr.cidr_block, private_ips)

        # -----------------------------
        # 2. 构建 payload
        # -----------------------------
        payload = {
            **data.model_dump(),
            "hashed_password": encrypt_text(data.password),
            "status": "RUNNING",
            "instance_id": f"cloud_server-{generate(size=12)}",
            "created_by": user_id,
            "created_by_name": username,
            "private_ip": private_ip
        }
        payload.pop("cidr_block", None)
        payload.pop("password", None)

        # -----------------------------
        # 3. 创建实例
        # -----------------------------
        instance = self.repo.create_instance_task(payload)
        if not instance:
            raise BusinessException(code=ErrorCode.FAILED, message="实例创建失败")

        # -----------------------------
        # 4. 账户检查 & 生成账单
        # -----------------------------
        account = self.account_service.account_exists(user_id)
        if not account:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        self.bill_service.create(
            user=user,
            account_id=account.id,
            resource_type="SERVER",
            charge_type=instance.charge_type,
            instance_id=instance.instance_id,
            instance=instance,
            unit_price=data.price,
        )

        # -----------------------------
        # 5. VPC / 子网 / 公网 IP / 系统盘 / 数据盘 / 资源组绑定
        # -----------------------------
        self.vpc_service.update_vpc(data.vpc_id, 'bind')
        self.subnet_service.update_subnet(data.vswitch_id, 'bind')

        public_ip = self.eip_service.allocate_eip(
            provider_code=data.cloud_provider_code,
            region_id=data.region_id,
            instance_id=instance.id,
            bind_instance_type='server'
        )
        instance.public_ip = public_ip

        # 系统盘
        system_disk_data = {
            "disk_name": gen_random_name('cbs-system'),
            "disk_type": "system",
            "description": f"系统盘，挂载到实例 {instance.instance_name}",
            "attached_device": "server",
            "attached_time": datetime.now(timezone.utc),
            "is_attached": bool(instance.id),
            "attached_instance_id": str(instance.id),
            "disk_category": data.system_disk_category,
            "disk_size": data.system_disk_size,
        }
        self.cbs_service.cbs_create_auto(user, 2.5, system_disk_data, instance)

        # 数据盘
        if data.data_disks:
            for disk in data.data_disks:
                disk_data = {
                    **disk.model_dump(),
                    "disk_name": gen_random_name('cbs-data'),
                    "disk_type": "data",
                    "description": f"数据盘，挂载到实例 {instance.instance_name}",
                    "attached_device": "server",
                    "attached_time": datetime.now(timezone.utc),
                    "attached_instance_id": str(instance.id),
                    "is_attached": bool(instance.id),
                    "disk_category": disk.disk_category,
                    "disk_size": disk.disk_size,
                }
                self.cbs_service.cbs_create_auto(user,2.5, disk_data, instance)

        # 资源组绑定
        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                created_by=user_id,
                created_by_name=username,
                resource_group_id=data.resource_group_id,
                resource_type="cloud_server",
                resource_id=str(instance.id),
            )
        )

        return instance

    def create_instance(self, user: dict, data: InstanceCreateSchema):
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
            action_mode="SERVER",
            action="CREATE",
            source_id_fn=lambda result: result.id if result else 0,
            source_id_on_fail=None,  # 失败就没有 source_id
            success_desc="云服务器创建成功",
            failed_desc="云服务器创建失败",
            func=_do
        )

    # 返回服务器列表
    def server_list_page(
        self,
        user_id: int,
        provider_code: str,
        region_id: str,
        zone_id: str,
        resource_group_id: str,
        instance_id: str,
        instance_name: str,
        instance_type: str,
        ip: str,
        status: str,
        ssh_proxy_port: int,
        page: int,
        page_size: int,
    ):
        items, total = self.repo.list_page(
            user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, instance_id,
            instance_name, instance_type, ip, status, ssh_proxy_port
        )

        return InstancePage(
            total=total,
            page=page,
            page_size=page_size,
            items=[InstanceBaseOut.model_validate(i) for i in items],
        )


    # 开机，关机，重启，
    def start_instance(self, data: InstanceActionSchema):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        instance.status = data.status
        instance.updated_at = datetime.now(timezone.utc)
        self.repo.commit()
        self.db.refresh(instance)
        return {"instance_id": instance.instance_id}


    # 修改服务器密码   hash_password
    def save_server_password(self, data: InstanceUpdatePassword):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        hashed_password = encrypt_text(data.password)
        result = self.repo.save_server_password(instance.instance_id, hashed_password)
        return result

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
            # -----------------------------
            # 5. VPC / 子网 / 公网 IP / 系统盘 / 数据盘 / 资源组绑定
            # -----------------------------
            self.vpc_service.update_vpc(instance.vpc_id, 'release')
            self.subnet_service.update_subnet(instance.vswitch_id, 'release')
            return result

    # 克隆
    def server_clone(self, user: dict, instance_id: int):
        # 事务 + 日志
        with self.db.begin():
            db_instance = self.repo.get_instance_by_find(instance_id)
            if not db_instance:
                raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

            bill_find = self.bill_service.bill_by_resource_id(db_instance.id)

            payload = InstanceCreateSchema(
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
                data_disks=db_instance.data_disks,
                os_type=db_instance.os_type,
                architecture=db_instance.architecture,
                hostname=db_instance.hostname,
                price=bill_find.unit_price,
                password='123456',
                enable_ssh_agent=db_instance.enable_ssh_agent,
            )
            return self._create_instance_internal(user, payload)

        # return self.repo.clone_instance(instance_id)

    # 转包年月  实例计费类型:PrePaid（包年包月）/PostPaid（按量付费）
    def save_charge_type(self, data: InstanceUpdateCharge):
        result = self.repo.save_charge_type(data.model_dump())
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return result

    # 更换镜像
    def save_image(self, data: InstanceUpdateImage):
        result = self.repo.save_image(data.model_dump())
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