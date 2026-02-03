from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp import ResourceGroup
from app.models.cmp.network_subnet import Subnet
from app.models.cmp.network_vpc import Vpc
from app.schemas.cmp.vpc_schema import VpcOut, VpcList


class VpcRepository:
    def __init__(self, db: Session):
        self.db = db

    #   批量插入
    def bulk_upsert(self, provider_code: str, region_id: str, vpcs: List[dict]):
        now = datetime.now(timezone.utc)
        for v in vpcs:
            vpc_id = v.get("VpcId")
            existing = (
                self.db.query(Vpc)
                .filter(
                    Vpc.cloud_provider_code == provider_code,
                    Vpc.region_id == region_id,
                    Vpc.id == v["id"],
                )
                .first()
            )
            if existing:
                existing.vpc_name = v.get("VpcName")
                existing.description = v.get("Description")
                existing.resource_group_id = v.get("ResourceGroupId")
                existing.updated_at = now
            else:
                new_vpc = Vpc(
                    vpc=vpc_id,
                    cloud_provider_code=provider_code,
                    region_id=region_id,
                    vpc_name=v.get("VpcName"),
                    description=v.get("Description"),
                    resource_group_id=v.get("ResourceGroupId"),
                    network_type=v.get("NetworkType", "VPC"),  # 阿里云一般是 VPC
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_vpc)
        self.db.commit()

    # --------------------------------
    # 创建单个 VPC
    # --------------------------------
    def create(self, data: dict):
        obj = Vpc(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    #   获取vpc列表
    def get_by_vpcs(self, user_id: int, provider_code: str, region_id: str):
        query = self.db.query(
            Vpc.id,
            Vpc.vpc_id,
            Vpc.vpc_name,
            Vpc.cloud_provider_code,
            Vpc.region_id,
            Vpc.resource_group_id,
            Vpc.network_type,
            Vpc.created_at,
            Vpc.updated_at,
            Vpc.description,
            Vpc.service_cidr,
            Vpc.status,
        )
        filters = [Vpc.created_by == user_id, Vpc.is_released == 0]
        if provider_code:
            filters.append(Vpc.cloud_provider_code == provider_code)
        if region_id:
            filters.append(Vpc.region_id == region_id)

        if filters:
            query = query.filter(*filters)

        items = query.order_by(Vpc.id.desc()).all()
        return [VpcOut.model_validate(i) for i in items]

    #   分页vpc列表数据
    def list_page(
        self, user_id: int, page: int, page_size: int,
        provider_code: Optional[str] = None, region_id: Optional[str] = None,
        resource_group_id: Optional[str] = None, vpc_name: Optional[str] = None
    ):
        query = self.db.query(
            Vpc.id,
            Vpc.vpc_id,
            Vpc.vpc_name,
            Vpc.cloud_provider_code,
            Vpc.region_id,
            Vpc.resource_group_id,
            Vpc.network_type,
            Vpc.created_at,
            Vpc.updated_at,
            Vpc.description,
            Vpc.service_cidr,
            Vpc.status,
            Vpc.sync_status,
            Vpc.used_count,
            ResourceGroup.rg_name.label("resource_group_name"),
            func.count(Subnet.id).label("subnet_count"),
        ).outerjoin(
            ResourceGroup,
            ResourceGroup.id == Vpc.resource_group_id
        ).outerjoin(
            Subnet,
            Subnet.vpc_id == Vpc.id,
        ).group_by(Vpc.id).order_by(Vpc.id.desc())

        filters = [Vpc.created_by == user_id, Vpc.is_released == 0]
        if provider_code:
            filters.append(Vpc.cloud_provider_code == provider_code)
        if region_id:
            filters.append(Vpc.region_id == region_id)
        if resource_group_id:
            filters.append(Vpc.resource_group_id == resource_group_id)
        if vpc_name:
            filters.append(Vpc.vpc_name.like(f"%{vpc_name}%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # vpc绑定
    def update_vpc(self, find: Vpc, data: dict):
        for key, value in data.items():
            if hasattr(find, key):
                setattr(find, key, value)
        return find

    # 释放（逻辑删除）
    def release(self, vpc: Vpc) -> bool:
        vpc.status = 'DELETED'
        vpc.is_released = 1
        # vpc.released_at = datetime.now(timezone.utc)
        self.db.add(vpc)
        self.db.commit()
        self.db.refresh(vpc)
        return True


    def get(self, vpc_id: int):
        return self.db.query(Vpc).filter_by(id=vpc_id).first()