# app/repos/cmp/instance_repo.py
from datetime import datetime, timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session
from nanoid import generate

from app.core.logger import logger
from app.models.cmp.cloud_server_instance import CloudServerInstance

from app.models.cmp.resource_group import ResourceGroup
from app.models.cmp.network_security_group import SecurityGroup

class ServerInstanceRepo:
    def __init__(self, db: Session):
        self.db = db

    def commit(self):
        self.db.commit()

    def refresh(self, obj):
        self.db.refresh(obj)

    # 服务器主表根据实例id查一条
    def get_instance_by_id(self, instance_id: str):
        return self.db.query(CloudServerInstance).filter(
            CloudServerInstance.instance_id == instance_id
        ).first()

    # 根据主表的自增id查一条
    def get_instance_by_find(self, instance_id: int):
        return self.db.query(CloudServerInstance).filter(CloudServerInstance.id == instance_id).first()

    # 创建服务器
    def create_instance_task(self, instance_data: dict) -> CloudServerInstance:
        instance_data.pop('price')
        instance = CloudServerInstance(**instance_data)
        self.db.add(instance)
        self.db.flush()  # 获取 instance.id
        return instance

    # 返回服务器分页列表
    def list_page(
        self,
        user_id: int,
        page: int,
        page_size: int,
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
    ):
        query = self.db.query(
            CloudServerInstance.instance_name,
            CloudServerInstance.description,
            CloudServerInstance.cloud_provider_code,
            CloudServerInstance.region_id,
            CloudServerInstance.zone_id,
            CloudServerInstance.resource_group_id,
            CloudServerInstance.instance_type,
            CloudServerInstance.instance_type_id,
            CloudServerInstance.image_id,
            CloudServerInstance.cpu,
            CloudServerInstance.gpu_memory,
            CloudServerInstance.gpu_amount,
            CloudServerInstance.gpu_spec,
            CloudServerInstance.system_disk_category,
            CloudServerInstance.system_disk_size,
            CloudServerInstance.charge_type,
            CloudServerInstance.period,
            CloudServerInstance.spot_strategy,
            CloudServerInstance.internet_charge_type,
            CloudServerInstance.internet_max_bandwidth_out,
            CloudServerInstance.vpc_id,
            CloudServerInstance.vswitch_id,
            CloudServerInstance.security_group_id,
            CloudServerInstance.ssh_proxy_port,
            CloudServerInstance.data_disks,
            CloudServerInstance.os_type,
            CloudServerInstance.architecture,
            CloudServerInstance.hostname,
            CloudServerInstance.id,
            CloudServerInstance.instance_id,
            CloudServerInstance.private_ip,
            CloudServerInstance.public_ip,
            CloudServerInstance.status,
            CloudServerInstance.sync_status,
            CloudServerInstance.enable_ssh_agent,
            CloudServerInstance.enable_protection,
            ResourceGroup.rg_name.label('resource_group_name'),
            SecurityGroup.sg_name.label('security_group_name'),
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == CloudServerInstance.resource_group_id
        ).outerjoin(
            SecurityGroup,
            SecurityGroup.id == CloudServerInstance.security_group_id
        ).order_by(CloudServerInstance.id.desc())

        filters = [CloudServerInstance.created_by == user_id, CloudServerInstance.is_released == 0]

        if provider_code:
            filters.append(CloudServerInstance.cloud_provider_code == provider_code)
        if region_id:
            filters.append(CloudServerInstance.region_id == region_id)
        if zone_id:
            filters.append(CloudServerInstance.zone_id == zone_id)
        if resource_group_id:
            filters.append(CloudServerInstance.resource_group_id == resource_group_id)
        if instance_id:
            filters.append(CloudServerInstance.instance_id.like(f'%{instance_id}%'))
        if instance_name:
            filters.append(CloudServerInstance.instance_name.like(f'%{instance_name}%'))
        if instance_type:
            filters.append(CloudServerInstance.instance_type == instance_type)
        if ip:
            filters.append(CloudServerInstance.public_ip == ip)
        if status:
            filters.append(CloudServerInstance.status == status)
        if ssh_proxy_port:
            filters.append(CloudServerInstance.ssh_proxy_port == ssh_proxy_port)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        # logger.info(f'这里是什么呢？ {items}')
        return items, total

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

    #   开启，关闭ssh代理
    def toggle_server_ssh(self, instance_id: int):
        db_instance = self.get_instance_by_find(instance_id)
        if not db_instance:
            return None
        db_instance.enable_ssh_agent ^= 1
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
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(db_instance)
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
            "released_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "instance_id": f"cloud_server-{generate(size=12)}"
        })

        # 创建新的实例对象
        new_instance = CloudServerInstance(**data)

        # 写入数据库
        self.db.add(new_instance)
        self.db.commit()
        self.db.refresh(new_instance)

        return True

    # 根据子网ip来查已创建的服务器的ip
    def get_find_by_subnet_id(self, subnet_id):
        items = (self.db.query(
            CloudServerInstance.vswitch_id,
            CloudServerInstance.private_ip,
            CloudServerInstance.public_ip,
        ).filter(
            CloudServerInstance.vswitch_id == subnet_id,
            CloudServerInstance.is_released == 0,
        ).all())
        return items

    #   转包年包月
    def save_charge_type(self, data: dict):
        instance_id: int = data.get('instance_id')
        find = self.get_instance_by_find(instance_id)
        if not find:
            return None
        find.charge_type = data['charge_type']
        find.period = data['period']
        find.auto_renew = data['auto_renew']
        self.db.commit()
        self.db.refresh(find)
        return True

    # 更换镜像
    def save_image(self, data: dict):
        instance_id: int = data['instance_id']
        find = self.get_instance_by_find(instance_id)
        if not find:
            return None
        find.image_id = data['image_id']
        self.db.commit()
        self.db.refresh(find)
        return True


