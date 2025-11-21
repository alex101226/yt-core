# app/services/cmp/subnet_service.py
from sqlalchemy.orm import Session
from typing import List
from nanoid import generate

from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.cmp.subnet_repo import SubnetRepository
from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage, SubnetBase
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.services.public.cloud_service import CloudService

class SubnetService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.subnet_repo = SubnetRepository(cmp_db)
        self.provider_repo = CloudProviderRepository(public_db)

    def sync_subnets(self, provider_code: str, region_id: str, vpc_id: str) -> List[SubnetBase]:
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )
        subnet_vpc = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )
        subnets = subnet_vpc.list_vswitches(provider_code, region_id, vpc_id)
        return subnets


    def create(self, data: SubnetCreate) -> SubnetOut:
        subnet_id = generate(size=12)  # 随机生成云子网ID
        obj = self.subnet_repo.create({**data.model_dump(), "subnet_id": subnet_id})
        return SubnetOut.model_validate(obj)

    def release(self, subnet_id: str, cloud_provider_code: str) -> SubnetOut:
        obj = self.subnet_repo.get(subnet_id, cloud_provider_code)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        obj = self.subnet_repo.release(obj)
        return SubnetOut.model_validate(obj)

    def page_subnets(
            self,
            cloud_provider_code: str = None,
            region_id: str = None,
            zone_id: str = None,
            vpc_id: str = None,
            resource_group_id: int = None,
            page: int = 1,
            page_size: int = 20
    ) -> SubnetPage:
        items, total = self.subnet_repo.list_page(
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            zone_id=zone_id,
            vpc_id=vpc_id,
            resource_group_id=resource_group_id,
            page=page,
            page_size=page_size
        )
        return SubnetPage(
            total=total,
            page=page,
            page_size=page_size,
            items=[SubnetOut.model_validate(s) for s in items]
        )
