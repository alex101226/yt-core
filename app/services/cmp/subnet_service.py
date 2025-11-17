# app/services/cmp/subnet_service.py
from sqlalchemy.orm import Session
from typing import List
from nanoid import generate

from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.cmp.subnet_repo import SubnetRepository
from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage
from app.common.status_code import ErrorCode
from app.common.messages import Message

class SubnetService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.subnet_repo = SubnetRepository(cmp_db)
        self.provider_repo = CloudProviderRepository(public_db)

    def sync_subnets(self, provider_code: str, region_id: str, vpc_id: str) -> List[SubnetOut]:
        existing_subnets = self.subnet_repo.list_by_vpc(vpc_id)
        if existing_subnets:
            logger.info(f"[{provider_code}][{region_id}] ip子网已存在数据库，无需同步")
            return existing_subnets

        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        client = CloudClientFactory.create_client(
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        # 3️⃣ 调用阿里云接口获取子网列表
        if provider_code == "aliyun":
            subnets = client.list_vswitches(region_id, vpc_id)
            # 增加 cloud_certificate_id 字段
            for s in subnets:
                s["cloud_certificate_id"] = provider.id
        else:
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND,
                message=Message.CLOUD_PROVIDER_NOT_FOUND
            )

        # 批量保存/更新到数据库
        self.subnet_repo.bulk_upsert(provider_code, region_id, vpc_id, subnets)

        db_subnets = self.subnet_repo.list_by_vpc(vpc_id)
        logger.info(f"[{provider_code}][{region_id}][{vpc_id}] 同步 {len(db_subnets)} 个子网")
        return db_subnets


    def create(self, data: SubnetCreate) -> SubnetOut:
        subnet_id = generate(size=12)  # 随机生成云子网ID
        obj = self.subnet_repo.create({**data.model_dump(), "subnet_id": subnet_id})
        return SubnetOut.model_validate(obj)

    def list_by_vpc(self, vpc_id: str) -> List[SubnetOut]:
        objs = self.subnet_repo.list_by_vpc(vpc_id)
        return [SubnetOut.model_validate(o) for o in objs]

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
