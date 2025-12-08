from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.eip import Eip
from app.schemas.cmp.eip_schema import EIPCreate

# eip的repository
class EipRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建eip
    def create_eip(self, user_id, data: EIPCreate):
        item = data.model_dump()
        item['user_id'] = user_id

        obj = Eip(**item)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return True

    #   分页列表
    def eip_page_list(
        self,
        page: int,
        page_size: int,
        provider_code: Optional[str] = None,
        region_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        resource_group_id: Optional[int] = None,
        eip_id: Optional[str] = None,
        public_ip: Optional[str] = None
    ):
        query = self.db.query(
            Eip.id,
            Eip.public_ip,
            Eip.created_at,
            Eip.updated_at,
            Eip.resource_group_id,
            Eip.cloud_provider_code,
            Eip.region_id,
            Eip.zone_id,
            Eip.description,
            Eip.eip_id,
            Eip.internet_charge_type,
            Eip.bandwidth,
            Eip.price,
            Eip.public_ip,
            Eip.bind_instance_id,
            Eip.status
        )
        # logger.info(f'查询 {query}')
        filters = []
        if provider_code is not None:
            filters.append(Eip.cloud_provider_code == provider_code)
        if region_id is not None:
            filters.append(Eip.region_id == region_id)
        if zone_id is not None:
            filters.append(Eip.zone_id == zone_id)
        if resource_group_id is not None:
            filters.append(Eip.resource_group_id == resource_group_id)
        if eip_id is not None:
            filters.append(Eip.eip_id.like(f"%{eip_id}%"))
        if public_ip is not None:
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
        # logger.info(f"eip_find.eip_id: {eip_id} {eip_find.status}")
        if eip_find is None:
            return None
        if status == 'RELEASING':
            eip_find.status = 'RELEASED'
            eip_find.last_operation = 'RELEASED'
        elif status == 'BINDING':
            eip_find.status = 'BOUND'
            eip_find.last_operation = 'BOUND'
        elif status == 'UNBINDING':
            eip_find.status = 'AVAILABLE'
            eip_find.last_operation = 'AVAILABLE'

        self.db.commit()
        self.db.refresh(eip_find)
        # logger.info(f'看下状态 {eip_find.status} {eip_find.last_operation}')
        return True


    # 根据eip的自增id
    def get_eip_by_id(self, eip_id: int) -> Optional[type[Eip]]:
        return self.db.query(Eip).filter_by(id = eip_id).first()



