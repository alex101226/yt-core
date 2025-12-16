from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp import ResourceGroup
from app.models.cmp.eip import Eip
from app.schemas.cmp.eip_schema import EIPCreate

# eip的repository
class EipRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建eip
    def create_eip(self, data: dict):
        obj = Eip(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj.id

    #   分页列表： 云厂商，云凭证，区域，可用区，按量付费，带宽上限，名称，资源组。
    def eip_page_list(
        self,
        user_id: int,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[str] = None,
        eip_id: Optional[str] = None,
        public_ip: Optional[str] = None
    ):
        query = self.db.query(
            Eip.id,
            Eip.eip_id,
            Eip.eip_name,
            Eip.public_ip,
            Eip.created_at,
            Eip.updated_at,
            Eip.resource_group_id,
            Eip.cloud_provider_code,
            Eip.region_id,
            Eip.zone_id,
            Eip.description,
            Eip.internet_charge_type,
            Eip.bandwidth,
            Eip.price,
            Eip.public_ip,
            Eip.bind_instance_id,
            Eip.status,
            Eip.sync_status,
            ResourceGroup.rg_name.label("resource_group_name")
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == Eip.resource_group_id
        )
        # logger.info(f'查询 {query}')
        filters = [Eip.created_by == user_id, Eip.is_released == 0]
        if provider_code:
            filters.append(Eip.cloud_provider_code == provider_code)
        if region_id:
            filters.append(Eip.region_id == region_id)
        if zone_id:
            filters.append(Eip.zone_id == zone_id)
        if resource_group_id:
            filters.append(Eip.resource_group_id == resource_group_id)
        if eip_id:
            filters.append(Eip.eip_id.like(f"%{eip_id}%"))
        if public_ip:
            filters.append(Eip.public_ip == public_ip)

        if filters:
            query = query.filter(*filters)
        count = query.count()
        offset_value = (page - 1) * page_size
        items = query.order_by(Eip.id.desc()).offset(offset_value).limit(page_size).all()
        return items, count

    # eip各种操作
    def eip_action(self, status: str, eip_id: int):
        eip_find = self.get_eip_by_id(eip_id)
        if eip_find is None:
            return None
        if eip_find.status == 'RELEASED':
            return None
        if status == 'RELEASING':
            eip_find.status = 'RELEASED'
            eip_find.last_operation = 'RELEASED'
            eip_find.is_released = 1
        elif status == 'BINDING':
            eip_find.status = 'BOUND'
            eip_find.last_operation = 'BOUND'
        elif status == 'UNBINDING':
            eip_find.status = 'AVAILABLE'
            eip_find.last_operation = 'AVAILABLE'

        self.db.commit()
        self.db.refresh(eip_find)
        return True


    # 根据eip的自增id
    def get_eip_by_id(self, eip_id: int) -> Optional[type[Eip]]:
        return self.db.get(Eip, eip_id)

    # 查询可用的eip
    def get_free_eip(self, provider_code: str, region_id: str):
        return (
            self.db.query(Eip)
            .filter(
                Eip.cloud_provider_code == provider_code,
                Eip.region_id == region_id,
                Eip.status == "AVAILABLE",
                Eip.is_released == 0,
            )
            .order_by(Eip.id.asc())
            .with_for_update()  # 🔒 防并发抢 IP
            .first()
        )



