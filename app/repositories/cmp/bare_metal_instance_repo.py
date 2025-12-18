from typing import Optional

from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.bare_metal_instance import BareMetalInstance

class BareMetalInstanceRepo:
    def __init__(self, db: Session):
        self.db = db

    # 创建裸金属
    def bare_metal_create(self, data: dict):
        instance = BareMetalInstance(**data)
        self.db.add(instance)
        self.db.flush()
        # self.db.commit()
        return instance


    # 裸金属分页
    def bare_metal_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        instance_id: Optional[str] = None,
        instance_name: Optional[str] = None,
        instance_type_id: Optional[str] = None,
        public_ip: Optional[str] = None,
        status: Optional[str] = None,
        ssh_proxy_port: Optional[int] = None,
    ):
        query = self.db.query(
            BareMetalInstance.id,
            BareMetalInstance.instance_name,
            BareMetalInstance.instance_id,
            BareMetalInstance.description,
            BareMetalInstance.cloud_provider_code,
            BareMetalInstance.region_id,
            BareMetalInstance.zone_id,
            BareMetalInstance.resource_group_id,
            BareMetalInstance.instance_type,
            BareMetalInstance.instance_type_id,
            BareMetalInstance.image_id,
            BareMetalInstance.cpu,
            BareMetalInstance.gpu_memory,
            BareMetalInstance.gpu_amount,
            BareMetalInstance.gpu_spec,
            BareMetalInstance.system_disk_category,
            BareMetalInstance.system_disk_size,
            BareMetalInstance.internet_charge_type,
            BareMetalInstance.instance_charge_type,
            BareMetalInstance.period,
            BareMetalInstance.internet_max_bandwidth_out,
            BareMetalInstance.auto_renew,
            BareMetalInstance.vpc_id,
            BareMetalInstance.vswitch_id,
            BareMetalInstance.security_group_id,
            BareMetalInstance.ssh_proxy_port,
            BareMetalInstance.os_type,
            BareMetalInstance.architecture,
            BareMetalInstance.hostname,
            BareMetalInstance.created_at,
            BareMetalInstance.updated_at,
            BareMetalInstance.is_released,
            BareMetalInstance.sync_status,
            BareMetalInstance.released_at,
            BareMetalInstance.status,
            BareMetalInstance.quantity,
        )
        filters = [BareMetalInstance.created_by == user_id, BareMetalInstance.is_released == 0]
        if provider_code:
            filters.append(BareMetalInstance.cloud_provider_code == provider_code)
        if region_id:
            filters.append(BareMetalInstance.region_id == region_id)
        if zone_id:
            filters.append(BareMetalInstance.zone_id == zone_id)
        if resource_group_id:
            filters.append(BareMetalInstance.resource_group_id == resource_group_id)
        if instance_id:
            filters.append(BareMetalInstance.instance_id.like(f'%{instance_id}%'))
        if instance_name:
            filters.append(BareMetalInstance.instance_name.like(f'%{instance_name}%'))
        if instance_type_id:
            filters.append(BareMetalInstance.instance_type_id.like(f'%{instance_type_id}%'))
        if public_ip:
            filters.append(BareMetalInstance.public_ip == public_ip)
        if status:
            filters.append(BareMetalInstance.status == status)
        if ssh_proxy_port:
            filters.append(BareMetalInstance.ssh_proxy_port.like(f'%{ssh_proxy_port}%'))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(BareMetalInstance.id.desc()).offset(offset_value).limit(page_size).all()
        return items, total

    # 根据子网ip来查已创建的服务器的ip
    def get_find_by_subnet_id(self, subnet_id):
        items = (self.db.query(
            BareMetalInstance.vswitch_id,
            BareMetalInstance.private_ip,
            BareMetalInstance.public_ip,
        ).filter(
            BareMetalInstance.vswitch_id==subnet_id,
            BareMetalInstance.is_released == 0,
        ).all())
        return items


