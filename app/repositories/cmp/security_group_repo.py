from typing import List, Optional
from sqlalchemy.orm import Session
from nanoid import generate

from app.models.public.cloud_certificate import CloudCertificate  # 示例模型
from app.models.cmp.security_group import SecurityGroup
from app.models.cmp.vpc import Vpc  # 假设你有 vpc 模型
from datetime import datetime, timezone

from app.schemas.cmp.security_group_schema import SecurityGroupSearch, SecurityGroupCreate, SecurityGroupOut


class SecurityGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def search(self, filters: SecurityGroupSearch):
        q = self.db.query(SecurityGroup)
        if filters.cloud_provider_code:
            q = q.filter(SecurityGroup.cloud_provider_code == filters.cloud_provider_code)
        if filters.region_id:
            q = q.filter(SecurityGroup.region_id == filters.region_id)
        if filters.resource_group_id:
            q = q.filter(SecurityGroup.resource_group_id == filters.resource_group_id)
        if filters.security_name:
            q = q.filter(SecurityGroup.security_name.like(f"%{filters.security_name}%"))
        q = q.order_by(SecurityGroup.created_at.desc())
        return q

    def bulk_upsert_from_cloud(self, provider_code: str, region_id: str, items: List[dict]):
        now = datetime.now(timezone.utc)
        upserted = []
        for v in items:
            cloud_group_id = v.get("SecurityGroupId") or v.get("SecurityGroupId")
            if not cloud_group_id:
                continue

            existing: Optional[SecurityGroup] = (
                self.db.query(SecurityGroup)
                .filter(SecurityGroup.cloud_group_id == cloud_group_id)
                .first()
            )

            # Determine local_vpc_id by matching cloud VpcId to local Vpc.cloud_vpc_id (your vpc table)
            cloud_vpc_id = v.get("VpcId")
            local_vpc = None
            if cloud_vpc_id:
                local_vpc = (
                    self.db.query(Vpc)
                    .filter(Vpc.vpc_id == cloud_vpc_id)
                    .first()
                )

            if existing:
                existing.security_name = v.get("SecurityGroupName") or existing.security_name
                existing.description = v.get("Description") or existing.description
                existing.resource_group_id = v.get("ResourceGroupId") or existing.resource_group_id
                existing.cloud_vpc_id = cloud_vpc_id or existing.cloud_vpc_id
                existing.vpc_id = local_vpc.id if local_vpc else existing.vpc_id
                existing.updated_at = now
                upserted.append(existing)
            else:
                new_obj = SecurityGroup(
                    id=None,  # if your model expects UUID, let DB / app generate; else remove
                    cloud_group_id=cloud_group_id,
                    cloud_provider_code=provider_code,
                    provider_code=provider_code,
                    credential_id=0,  # you may want to fill credential id from context
                    region_id=region_id,
                    security_name=v.get("SecurityGroupName") or "",
                    description=v.get("Description"),
                    resource_group_id=v.get("ResourceGroupId"),
                    cloud_vpc_id=cloud_vpc_id,
                    vpc_id=local_vpc.id if local_vpc else None,
                    created_at=now,
                    updated_at=now,
                )
                self.db.add(new_obj)
                upserted.append(new_obj)

        self.db.commit()
        # refresh appended objects if needed
        return upserted

    # --------------------------
    # 创建安全组（仅主表）
    # --------------------------
    def create_group(self, data: SecurityGroupCreate):
        sg = SecurityGroup(
            id=generate(size=12),
            security_name=data.security_name,
            description=data.description,
            cloud_provider_code=data.cloud_provider_code,
            cloud_certificate_id=data.cloud_certificate_id,
            region_id=data.region_id,
            vpc_id=data.vpc_id,
            cloud_group_id=None,
            sync_status=0,
            is_released=False,
        )
        self.db.add(sg)
        self.db.commit()
        self.db.refresh(sg)
        return sg

    # --------------------------
    # 标记释放
    # --------------------------
    def mark_released(self, group_id: str):
        sg = self.db.query(SecurityGroup).filter(SecurityGroup.id == group_id).first()
        if not sg:
            return None
        sg.is_released = True
        sg.released_at = datetime.now(timezone.utc)
        sg.sync_status = 3
        self.db.commit()
        return sg

    #   根据id获取数据
    def get_by_id(self, group_id: str) -> Optional[type[SecurityGroup]]:
        return self.db.query(SecurityGroup).filter(
            SecurityGroup.id == group_id,
        SecurityGroup.is_released==0
        ).first()

    #   根据云厂商获取数据
    # SecurityGroupRepository
    def get_credential_by_sg(self, sg_id: str):
        sg = self.db.query(SecurityGroup).filter(
            SecurityGroup.id == sg_id,
            SecurityGroup.is_released == 0
        ).first()

        if not sg:
            return None

        # 这里是 cloud_credential_id
        cred_id = sg.cloud_credential_id
        if not cred_id:
            return None

        return self.db.query(CloudCertificate).filter_by(id = cred_id).first()


    #   返回安全组的列表数据
    def get_by_security_group(self, provider_code: str, region_id: str, vpc_id: int) -> List[SecurityGroup]:
        return self.db.query(SecurityGroup).filter(
            SecurityGroup.is_released == 0,
            SecurityGroup.cloud_provider_code == provider_code,
            SecurityGroup.region_id == region_id,
            SecurityGroup.vpc_id==vpc_id
        ).all()

