# app/repositories/cmp/subnet_repo.py
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.subnet import Subnet
from app.schemas.cmp.subnet_schema import SubnetOut, SubnetBase

from app.models.cmp.vpc import Vpc
from app.models.cmp import ResourceGroup

class SubnetRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_upsert(self, provider_code: str, region_id: str, vpc_id: str, subnets: List[SubnetBase]):
        """
        批量插入或更新子网
        :param provider_code: 云厂商
        :param region_id: 区域ID
        :param vpc_id: VPC ID
        :param subnets: 子网列表，每个字典包含 vswitch_id, vswitch_name, cidr_block, zone_id
        """
        now = datetime.now(timezone.utc)
        for s in subnets:
            subnet_id = s.get("vswitch_id")
            existing = (
                self.db.query(Subnet)
                .filter(
                    Subnet.cloud_provider_code == provider_code,
                    Subnet.region_id == region_id,
                    Subnet.vpc_id == vpc_id,
                    Subnet.subnet_id == subnet_id,
                )
                .first()
            )
            if existing:
                existing.subnet_name = s.get("vswitch_name")
                existing.cidr_block = s.get("cidr_block")
                existing.zone_id = s.get("zone_id")
                existing.updated_at = now
            else:
                new_subnet = Subnet(
                    subnet_id=subnet_id,
                    subnet_name=s.get("vswitch_name"),
                    vpc_id=vpc_id,
                    cloud_provider_code=provider_code,
                    cloud_certificate_id=s.get("cloud_certificate_id"),
                    region_id=region_id,
                    zone_id=s.get("zone_id"),
                    cidr_block=s.get("cidr_block"),
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_subnet)
        self.db.commit()

    def create(self, data: dict) -> bool:
        obj = Subnet(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj.id

    def get(self, subnet_id: str) -> Optional[Subnet]:
        return (
            self.db.query(Subnet)
            .filter_by(id=subnet_id)
            .first()
        )

    #   返回list
    def list_by_subnet(self, user_id: int, vpc_id: int) -> list[type[Subnet]]:
        items = self.db.query(Subnet).filter(
            Subnet.user_id == user_id,
            Subnet.vpc_id==vpc_id
        ).order_by(Subnet.created_at).all()
        return items


    #   返回list
    def vpc_by_subnet_page_list(self, vpc_id: int, page: int, page_size: int) -> tuple[int, list[type[Subnet]]]:
        query = self.db.query(Subnet)
        total = query.count()
        items = query.filter_by(vpc_id=vpc_id).offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # 释放
    def release(self, obj: Subnet) -> bool:
        obj.is_released = 1
        # obj.released_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(obj)
        return True

    # 分页查询
    def list_page(
        self,
        user_id: int,
        cloud_provider_code: str = None,
        region_id: str = None,
        zone_id: str = None,
        vpc_id: str = None,
        resource_group_id: str = None,
        page: int = 1,
        page_size: int = 20
    ):
        query = self.db.query(
            Subnet.id,
            Subnet.subnet_id,
            Subnet.subnet_name,
            Subnet.cidr_block,
            Subnet.description,
            Subnet.resource_group_id,
            Subnet.cloud_provider_code,
            Subnet.region_id,
            Subnet.zone_id,
            Subnet.vpc_id,
            Subnet.is_released,
            Subnet.released_at,
            Subnet.created_at,
            Subnet.updated_at,
            Subnet.sync_status,
            ResourceGroup.rg_name.label("resource_group_name"),
            Vpc.vpc_name.label("vpc_name"),
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == Subnet.resource_group_id
        ).outerjoin(
            Vpc,
            Vpc.id == Subnet.vpc_id
        )
        filters = [Subnet.user_id == user_id, Subnet.is_released == 0]

        if cloud_provider_code:
            filters.append(Subnet.cloud_provider_code == cloud_provider_code)
        if region_id:
            filters.append(Subnet.region_id == region_id)
        if zone_id:
            filters.append(Subnet.zone_id == zone_id)
        if vpc_id:
            filters.append(Subnet.vpc_id == vpc_id)
        if resource_group_id:
            filters.append(Subnet.resource_group_id == resource_group_id)

        if filters:
            query = query.filter(and_(*filters))

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        # logger.info(f'看下这个列表 {items}')
        return items, total
