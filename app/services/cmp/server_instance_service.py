# app/services/cmp/instance_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from nanoid import generate

from app.repositories.cmp.server_instance_repo import ServerInstanceRepo
# from app.schemas.cmp.server_instance_schema import InstancePage, InstanceBaseOut
from app.core.security import hash_password

from app.common.ipaddress import allocate_private_ip

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.logger import logger

class InstanceService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ServerInstanceRepo(db)
    # 创建服务器
    def create_instance(self, schema: dict):
        # 1️⃣ 构造主表数据
        hashed_password = hash_password(schema['password'])
        schema['password'] = hashed_password

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

        # 2️⃣ 创建数据盘任务
        if schema['data_disks']:
            self.repo.create_disk_tasks(instance_task.id, schema['data_disks'])

        # 6️⃣ 创建状态检查任务（初始 pending）
        self.repo.create_status_check_task(
            main_task_id=instance_task.id,
            instance_id=instance_task.instance_id or "",  # 还没生成云端实例，可以先空
            check_count=0,
            max_check=30,
            status=1  # PENDING
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
        resource_group_id: int,
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
    def start_instance(self, status, instance_id: str, user_id: int):
        # 1️⃣ 创建操作任务
        instance = self.repo.get_instance_by_id(instance_id)
        if not instance:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        instance.status = status.value
        instance.last_operation = status.value
        instance.updated_at = datetime.now(timezone.utc)
        self.repo.commit()

        # 创建轮询任务
        self.repo.create_status_check_task(
            main_task_id=instance.id,
            instance_id=instance_id,
            check_count=0,
            max_check=10,
            status=1
        )
        self.repo.commit()
        return {"instance_id": instance_id}
