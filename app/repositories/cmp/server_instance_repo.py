# app/repos/cmp/instance_repo.py
from sqlalchemy import and_

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.instance_create_task import InstanceCreateTask
from app.models.cmp.volume_create_task import VolumeCreateTask

class ServerInstanceRepo:
    def __init__(self, db: Session):
        self.db = db

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
            disk_task = VolumeCreateTask(
                main_task_id=instance_id,
                disk_category=d["disk_category"],
                disk_size=d["disk_size"],
                encrypted=d.get("encrypted", False)
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
        logger.info(f'这里是什么呢？ {items}')
        return items, total