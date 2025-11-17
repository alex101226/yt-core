from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session
from app.models.cmp.vpc import Vpc
from app.schemas.cmp.vpc_schema import VpcOut


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
    def create(self, data: dict) -> Vpc:
        obj = Vpc(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    #   获取vpc列表
    def get_by_vpcs(self, provider_code: str, region_id: str) -> List[VpcOut]:
        return (
            self.db.query(Vpc)
            .filter(
                Vpc.cloud_provider_code == provider_code,  # type: ignore
                Vpc.region_id == region_id  # type: ignore
            )
            .order_by(Vpc.id.desc())
            .all()
        )

    #   分页vpc列表数据
    def list_page(self, provider_code: str, region_id: str, page: int, page_size: int):
        query = self.db.query(Vpc).filter(
            Vpc.cloud_provider_code == provider_code,
            Vpc.region_id == region_id,
        ).order_by(Vpc.id.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # 释放（逻辑删除）
    def release(self, vpc: Vpc) -> VpcOut:
        vpc.is_released = True
        vpc.released_at = datetime.now(timezone.utc)
        self.db.add(vpc)
        self.db.commit()
        self.db.refresh(vpc)
        return vpc


    def get(self, vpc_id: int) -> Vpc:
        return self.db.query(Vpc).get(vpc_id)