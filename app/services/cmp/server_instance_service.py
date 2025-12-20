# app/services/cmp/instance_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

from app.common.ipaddress import allocate_private_ip
from app.core.security import hash_password

from app.services.cmp.eip_service import EIPService

from app.services.cmp.resource_group_service import ResourceGroupService
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

from app.services.cmp.cbs_service import CbsService
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate

from app.repositories.cmp.server_instance_repo import ServerInstanceRepo
from app.schemas.cmp.server_instance_schema import (
InstanceActionSchema, InstanceUpdatePassword, InstanceCreateSchema, InstanceBaseOut, InstancePage
)

class InstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServerInstanceRepo(db)
        self.cbs_service = CbsService(db)
        self.resource_bind_service = ResourceGroupService(db)
        self.eip_service = EIPService(db)

    # 创建服务器
    def create_instance(self, user_id: int, data: InstanceCreateSchema):
        # 先查子网
        subnet_all = self.repo.get_find_by_subnet_id(data.vswitch_id)
        private_ips = {row.private_ip for row in subnet_all}

        # 默认开启释放保护
        # schema['enable_protection'] = 1
        # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
        cidr = data.cidr_block
        private_ip = ''
        if cidr:
            # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
            private_ip = allocate_private_ip(cidr, private_ips)

        payload = {
            **data.model_dump(),
            "hashed_password": hash_password(data.password),
            "status": "RUNNING",
            "last_operation": "RUNNING",
            "instance_id": f"cloud_server-{generate(size=12)}",
            "created_by": user_id,
            "private_ip": private_ip
        }

        # ⭐ 3) payload 中删除 cidr_block
        payload.pop("cidr_block", None)
        payload.pop("password", None)

        instance = self.repo.create_instance_task(payload)
        if not instance:
            return False

        # 5. 是否需要公网 IP
        public_ip = self.eip_service.allocate_eip(
            provider_code=data.cloud_provider_code,
            region_id=data.region_id,
            instance_id=instance.id,
            internet_charge_type=data.internet_charge_type,
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
            "disk_type": "system",  # 磁盘类型：system 系统盘 / data 数据盘。
            "disk_category": data.system_disk_category, # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
            "disk_size": data.system_disk_size, # 磁盘大小
            "charge_type": data.instance_charge_type,   # 计费方式：PrePaid 包年包月 / PostPaid 按量付费
            "period": data.period or 1, #   包年月的月份
            "auto_renew": False,
            "attached_instance_id": str(instance.id),   # 挂载的实例 ID（ecs/lh/lb）
            "attached_device": data.instance_name, #   挂载点名称，如 /dev/vdb
            "attached_time": datetime.now(timezone.utc).isoformat(),  # 挂载时间
            # "status": "InUse",  # 系统盘创建后直接挂载
            "description": f"系统盘，挂载到实例 {instance.instance_name}",
            "tags": []
        }
        self.cbs_service.cbs_create_s(user_id, CbsDiskCreate(**system_disk_data))

        # -----------------------------
        # 3. 创建数据盘 CBS
        # -----------------------------
        if data.data_disks:
            for disk in data.data_disks:
                disk_data = {
                    "cloud_provider_code": data.cloud_provider_code,
                    "region_id": data.region_id,
                    "zone_id": data.zone_id,
                    "resource_group_id": data.resource_group_id,
                    "disk_type": "data",  # 磁盘类型：system 系统盘 / data 数据盘。
                    "disk_category": disk.system_disk_category, # 磁盘种类，例如：cloud、cloud_ssd、cloud_essd_pl0 等
                    "disk_size": disk.system_disk_size, # 磁盘大小
                    "charge_type": data.instance_charge_type,   # 计费方式：PrePaid 包年包月 / PostPaid 按量付费
                    "period": data.period or 1, #   包年月的月份
                    "auto_renew": False,
                    "attached_instance_id": str(instance.id),   # 挂载的实例 ID（ecs/lh/lb）
                    "attached_device": data.instance_name, #   挂载点名称，如 /dev/vdb
                    "attached_time": datetime.now(timezone.utc).isoformat(),  # 挂载时间
                    # "status": "InUse",  # 系统盘创建后直接挂载
                    "description": f"系统盘，挂载到实例 {instance.instance_name}",
                    "tags": []
                }
                self.cbs_service.cbs_create_s(user_id, CbsDiskCreate(**disk_data))

        #   绑定安全组
        self.resource_bind_service.bind(
            ResourceGroupBindingCreate(
                cloud_provider_code=data.cloud_provider_code,
                user_id=user_id,
                resource_group_id=data.resource_group_id,
                resource_type="cloud_server",
                resource_id=str(instance.id),
            )
        )

        # 6️⃣ 创建状态检查任务（初始 pending）
        # self.repo.create_status_check_task(
        #     main_task_id=instance_task.id,
        #     instance_id=instance_task.instance_id or "",  # 还没生成云端实例，可以先空
        #     check_count=0,
        #     max_check=30,
        #     status="PENDING"
        # )

        # 3️⃣ 提交事务
        self.repo.commit()
        self.repo.refresh(instance)

        return True


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
        status: int,
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
        # 1️⃣ 创建操作任务
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        instance.status = data.status
        instance.last_operation = data.status
        instance.updated_at = datetime.now(timezone.utc)
        self.repo.commit()

        # 创建轮询任务
        self.repo.create_status_check_task(
            main_task_id=instance.id,
            instance_id=instance.instance_id,
            check_count=0,
            max_check=10,
            status=1
        )
        self.repo.commit()
        return {"instance_id": instance.instance_id}


    # 修改服务器密码   hash_password
    def save_server_password(self, data: InstanceUpdatePassword):
        instance = self.repo.get_instance_by_find(data.instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        hashed_password = hash_password(data.password)
        result = self.repo.save_server_password(instance.instance_id, hashed_password)
        return result

    # 开启/关闭释放保护
    def toggle_server_release(self, instance_id: int, user_id: int):
        instance = self.repo.get_instance_by_find(instance_id)
        if instance.user_id != user_id:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return self.repo.toggle_server_release(instance_id)

    # 释放
    def server_release(self, instance_id: int):
        instance = self.repo.get_instance_by_find(instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if instance.enable_protection == 1:
           raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="此服务器无法释放")

        active_status = {
            'STARTING',
            'CREATING',
            'RUNNING',
            'DEPLOYING',
            'DISK_EXPANDING',
            'PREPARE_REBOOT'
        }

        if instance.status in active_status:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="当前服务器正在使用，无法释放")
        return self.repo.server_release(instance_id)

    # 克隆
    def server_clone(self, instance_id: int):
        db_instance = self.repo.get_instance_by_find(instance_id)
        if not db_instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return self.repo.clone_instance(instance_id)