# app/services/cmp/instance_service.py
from sqlalchemy.orm import Session
from app.repositories.cmp.server_instance_repo import ServerInstanceRepo
from app.schemas.cmp.server_instance_schema import InstancePage, InstanceBaseOut
from app.core.security import hash_password

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
        instance = self.repo.create_instance_task(schema)

        # 2️⃣ 创建数据盘任务
        if schema['data_disks']:
            self.repo.create_disk_tasks(instance.id, schema['data_disks'])

        # 3️⃣ 提交事务
        self.db.commit()
        self.db.refresh(instance)
        return instance


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
