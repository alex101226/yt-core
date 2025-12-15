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

from app.repositories.cmp.cbs_repo import CbsDiskRepository
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate

from app.repositories.cmp.server_instance_repo import ServerInstanceRepo
from app.schemas.cmp.server_instance_schema import InstanceActionSchema, InstanceUpdatePassword

class InstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServerInstanceRepo(db)
        self.cbs_repo = CbsDiskRepository(db)

    # 创建服务器
    def create_instance(self, schema: dict):
        # 1️⃣ 构造主表数据
        hashed_password = hash_password(schema['password'])
        schema['password'] = hashed_password
        # 默认开启释放保护
        # schema['enable_protection'] = 1
        # ⭐ 2) 处理私网 IP（如果没有传 private_ip）
        if not schema.get("private_ip"):
            cidr = schema.get("cidr_block")
            if cidr:
                # 获取子网已占用的 IP（TODO: 你后面可以接阿里云 API）
                used_ips = []
                private_ip = allocate_private_ip(cidr, used_ips)
                schema["private_ip"] = private_ip

        # ⭐ 3) schema 中删除 cidr_block，避免无效字段传入 SQLAlchemy
        schema.pop("cidr_block", None)
        schema['status'] = 'INIT'
        schema['last_operation'] = 'INIT'
        schema['instance_id'] = f"ECS-{generate(size=6)}"
        instance_task = self.repo.create_instance_task(schema)

        # -----------------------------
        # 2. 创建系统盘 CBS
        # -----------------------------
        system_disk_data = {
            "disk_id": f"CBS-{generate(size=8)}",
            "cloud_provider_code": schema['cloud_provider_code'],
            "region_id": schema['region_id'],
            "zone_id": schema.get('zone_id'),
            "resource_group_id": schema.get('resource_group_id', 0),
            "disk_type": "system",
            "disk_category": schema['system_disk_category'],
            "disk_size": schema['system_disk_size'],
            "charge_type": schema['instance_charge_type'],
            "period": schema.get('period'),
            "attached_instance_id": instance_task.instance_id,
            "status": "InUse",  # 系统盘创建后直接挂载
            "description": f"系统盘，挂载到实例 {instance_task.instance_name}"
        }
        self.cbs_repo.cbs_create(schema['user_id'], CbsDiskCreate(**system_disk_data))

        # -----------------------------
        # 3. 创建数据盘 CBS
        # -----------------------------
        if schema.get('data_disks'):
            for disk in schema['data_disks']:
                disk_data = {
                    "disk_id": f"CBS-{generate(size=8)}",
                    "cloud_provider_code": schema['cloud_provider_code'],
                    "region_id": schema['region_id'],
                    "zone_id": schema.get('zone_id'),
                    "resource_group_id": schema.get('resource_group_id', 0),
                    "disk_type": "data",
                    "disk_category": disk['disk_category'],
                    "disk_size": disk['disk_size'],
                    "charge_type": schema['instance_charge_type'],
                    "period": schema.get('period'),
                    "attached_instance_id": instance_task.instance_id,
                    "status": "InUse",  # 数据盘创建后直接挂载
                    "description": disk.get('description', f"数据盘，挂载到实例 {instance_task.instance_name}")
                }
                self.cbs_repo.cbs_create(schema['user_id'], CbsDiskCreate(**disk_data))
                # 2️⃣ 创建数据盘任务
                # self.repo.create_disk_tasks(instance_task.instance_id, schema['data_disks'])
        # 6️⃣ 创建状态检查任务（初始 pending）
        self.repo.create_status_check_task(
            main_task_id=instance_task.id,
            instance_id=instance_task.instance_id or "",  # 还没生成云端实例，可以先空
            check_count=0,
            max_check=30,
            status="PENDING"
        )

        # 3️⃣ 提交事务
        self.repo.commit()
        self.repo.refresh(instance_task)
        return instance_task


    # 返回服务器列表
    def server_list_page(
        self,
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
            provider_code, region_id, zone_id, resource_group_id, instance_id,
            instance_name, instance_type, ip, status, ssh_proxy_port, page, page_size
        )

        return {
            "page": page,
            "total": total,
            "items": items,
            "page_size": page_size,
        }


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