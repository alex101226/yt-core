# app/repos/cmp/instance_repo.py
from datetime import datetime, timezone

from sqlalchemy import and_

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp import InstanceStatusCheckTask
from app.models.cmp.instance_create_task import InstanceCreateTask
from app.models.cmp.disk_provision_task import DiskProvisionTask

class ServerInstanceRepo:
    def __init__(self, db: Session):
        self.db = db

    def commit(self):
        self.db.commit()

    def refresh(self, obj):
        self.db.refresh(obj)

    # 服务器主表根据实例id查一条
    def get_instance_by_id(self, instance_id: str):
        return self.db.query(InstanceCreateTask).filter(
            InstanceCreateTask.instance_id == instance_id
        ).first()

    # 根据主表的自增id查一条
    def get_instance_by_find(self, instance_id: int):
        return self.db.query(InstanceCreateTask).filter(InstanceCreateTask.id == instance_id).first()

    # 创建服务器
    def create_instance_task(self, instance_data: dict) -> InstanceCreateTask:
        instance = InstanceCreateTask(**instance_data)
        self.db.add(instance)
        self.db.flush()  # 获取 instance.id
        return instance

    # 创建数据盘
    def create_disk_tasks(self, instance_id: int, disks: list):
        disk_objs = []
        for d in disks:
            disk_task = DiskProvisionTask(
                main_task_id=instance_id,
                disk_category=d["disk_category"],
                disk_size=d["disk_size"],
                encrypted=d.get("encrypted", False),
                status="SUCCESS"
            )
            self.db.add(disk_task)
            disk_objs.append(disk_task)
        return disk_objs


    # 返回服务器分页列表
    def list_page(
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
        query = self.db.query(
            InstanceCreateTask.id,
            InstanceCreateTask.instance_id,
            InstanceCreateTask.instance_name,
            InstanceCreateTask.instance_type,
            # InstanceCreateTask.ip,
            InstanceCreateTask.status,
            InstanceCreateTask.ssh_proxy_port,
            InstanceCreateTask.zone_id,
            InstanceCreateTask.resource_group_id,
            InstanceCreateTask.cloud_provider_code,
            InstanceCreateTask.image_id,
            InstanceCreateTask.system_disk_category,
            InstanceCreateTask.system_disk_size,
            InstanceCreateTask.instance_charge_type,
            InstanceCreateTask.period,
            InstanceCreateTask.spot_strategy,
            InstanceCreateTask.internet_charge_type,
            InstanceCreateTask.internet_max_bandwidth_out,
            InstanceCreateTask.vpc_id,
            InstanceCreateTask.vswitch_id,
            # InstanceCreateTask.cidr_block,
            InstanceCreateTask.security_group_id,
            InstanceCreateTask.hostname,
            InstanceCreateTask.description,
            InstanceCreateTask.password,
            InstanceCreateTask.key_pair_name,
            InstanceCreateTask.enable_ssh_agent,
            InstanceCreateTask.enable_protection,
            InstanceCreateTask.resource_group_id,
            InstanceCreateTask.data_disks
        )

        filters = []

        if provider_code:
            filters.append(InstanceCreateTask.cloud_provider_code == provider_code)
        if region_id:
            filters.append(InstanceCreateTask.region_id == region_id)
        if zone_id:
            filters.append(InstanceCreateTask.zone_id == zone_id)
        if resource_group_id:
            filters.append(InstanceCreateTask.resource_group_id == resource_group_id)
        if instance_id:
            filters.append(InstanceCreateTask.instance_id == instance_id)
        if instance_name:
            filters.append(InstanceCreateTask.instance_name == instance_name)
        if instance_type:
            filters.append(InstanceCreateTask.instance_type == instance_type)
        if ip:
            filters.append(InstanceCreateTask.private_ip == ip)
        if status:
            filters.append(InstanceCreateTask.status == status)
        if ssh_proxy_port:
            filters.append(InstanceCreateTask.ssh_proxy_port == ssh_proxy_port)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        # logger.info(f'这里是什么呢？ {items}')
        return items, total


    # 创建轮训任务
    def create_status_check_task(self, main_task_id: int, instance_id: str, check_count=0, max_check=10, status="PENDING"):
        task = InstanceStatusCheckTask(
            main_task_id=main_task_id,
            instance_id=instance_id,
            check_count=check_count,
            max_check=max_check,
            status=status
        )
        self.db.add(task)
        self.db.flush()
        return task


    # 修改密码
    def save_server_password(self, instance_id: int, password: str):
        db_instance = self.get_instance_by_find(instance_id)
        if not db_instance:
            return None

        db_instance.password = password
        self.db.commit()
        self.db.refresh(db_instance)
        return True

    # 关闭释放保护
    def toggle_server_release(self, instance_id: int):
        db_instance = self.get_instance_by_find(instance_id)
        if not db_instance:
            return None

        db_instance.enable_protection ^= 1   # 位运算异或，直接 0→1、1→0
        self.db.commit()
        self.db.refresh(db_instance)
        return True

    # 释放
    def server_release(self, instance_id: int):
        db_instance = self.get_instance_by_find(instance_id)
        if not db_instance:
            return None
        db_instance.status = 'RELEASED'
        db_instance.is_released = 1
        self.db.commit()
        self.db.refresh(db_instance)
        return True

    # 克隆
    def clone_instance(self, instance_id: int):
        """克隆服务器主实例"""
        old_instance = self.get_instance_by_find(instance_id)
        if not old_instance:
            return None

        # 需要排除的字段（不会 copy）
        exclude_fields = {
            "id",
            "instance_id",
            "created_at",
            "updated_at",
            "released_at",
        }

        # 将 SQLAlchemy 对象转成 dict
        data = {
            column.name: getattr(old_instance, column.name)
            for column in old_instance.__table__.columns
            if column.name not in exclude_fields
        }

        # 覆盖克隆规则要求的字段
        data.update({
            "status": "INIT",
            "sync_status": 1,
            "is_released": 0,
            "instance_id": None,
            "last_operation": "INIT",
            "released_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

        # 创建新的实例对象
        new_instance = InstanceCreateTask(**data)

        # 写入数据库
        self.db.add(new_instance)
        self.db.commit()
        self.db.refresh(new_instance)

        return True
