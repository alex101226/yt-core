# app/services/public/cloud_vpc_service.py
from typing import List
from sqlalchemy.orm import Session
# from nanoid import generate

from app.schemas.cmp.vpc_schema import VpcOut, VpcCreate
from app.clients.cloud_client_factory import CloudClientFactory
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.cmp.vpc_repo import VpcRepository
from app.core.logger import logger
from app.common.status_code import ErrorCode
from app.common.messages import Message

class VPCService:
    """
    VPC 服务层：提供业务逻辑处理
    """

    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.provider_repo = CloudProviderRepository(public_db)
        self.vpc_repo = VpcRepository(cmp_db)

    """
    获取指定 Region 的 VPC 列表
    """
    def sync_vpcs(self, provider_code: str, region_id: str) -> List[VpcOut]:
        existing_vpc = self.lis_vpcs(provider_code, region_id)
        if existing_vpc:
            logger.info(f"[{provider_code}][{region_id}] vpc已存在数据库，无需同步")
            return existing_vpc

        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        client = CloudClientFactory.create_client(
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        # 3️⃣ 调用客户端方法获取vpc列表
        if provider_code == "aliyun":
            vpcs = client.list_vpcs(region_id)
        # elif provider_code == "tencentcloud":
        #     zones = client.list_zones(region_id)
        else:
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND,
                message=Message.CLOUD_PROVIDER_NOT_FOUND
            )

        self.vpc_repo.bulk_upsert(provider_code, region_id, vpcs)

        db_vpc = self.lis_vpcs(provider_code, region_id)
        logger.info(f"[{provider_code}][{region_id}] 同步 {len(db_vpc)} 个vpc")
        return db_vpc

    #   返回数据库的vpc
    def lis_vpcs(self, provider_code: str, region_id: str) -> List[VpcOut]:
        return self.vpc_repo.get_by_vpcs(provider_code, region_id)

    # 返回带分页的vpc
    def list_page(self, provider_code: str, region_id: str, page: int, page_size: int):
        return self.vpc_repo.list_page(provider_code, region_id, page, page_size)

        # --------------------------------
        # 创建单个 VPC
        # --------------------------------

    def create(self, data: VpcCreate) -> VpcOut:
        obj = self.vpc_repo.create(data.model_dump())
        return VpcOut.model_validate(obj)

    # 释放逻辑
    def release(self, vpc_id: int) -> VpcOut:
        vpc = self.vpc_repo.get(vpc_id)
        if not vpc:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if vpc.is_released:
            raise BusinessException(code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND, message= '该 VPC 已释放，无需重复释放')

        vpc = self.vpc_repo.release(vpc)
        return VpcOut.model_validate(vpc)