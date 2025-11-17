# app/repositories/cmp/subnet_repo.py
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.models.cmp.subnet import Subnet
from app.schemas.cmp.subnet_schema import SubnetOut


class SubnetRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_upsert(self, provider_code: str, region_id: str, vpc_id: str, subnets: List[dict]):
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

    def create(self, data: dict) -> Subnet:
        obj = Subnet(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get(self, subnet_id: str, cloud_provider_code: str) -> Optional[Subnet]:
        return (
            self.db.query(Subnet)
            .filter_by(subnet_id=subnet_id, cloud_provider_code=cloud_provider_code)
            .first()
        )

    def list_by_vpc(self, vpc_id: str) -> List[SubnetOut]:
        return self.db.query(Subnet).filter(Subnet.vpc_id==vpc_id).order_by(Subnet.id.desc()).all()

    def release(self, obj: Subnet):
        obj.is_released = True
        obj.released_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # 分页查询
    def list_page(
            self,
            cloud_provider_code: str = None,
            region_id: str = None,
            zone_id: str = None,
            vpc_id: str = None,
            resource_group_id: int = None,
            page: int = 1,
            page_size: int = 20
    ) -> tuple[list[type[Subnet]], int]:
        """
        分页查询子网
        :return: 返回子网列表及总数
        """
        query = self.db.query(Subnet)
        filters = []

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
        return items, total
