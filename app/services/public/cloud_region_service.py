# app/services/public/cloud_region_service.py
from typing import List
from sqlalchemy.orm import Session

from app.clients.cloud_client_factory import CloudClientFactory
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.public.cloud_region_repo import CloudRegionRepository
from app.models.public.cloud_region import CloudRegion
from app.core.logger import logger

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode

class CloudRegionService:
    """云厂商区域同步与查询服务"""
    def __init__(self, db: Session):
        self.provider_repo = CloudProviderRepository(db)
        self.region_repo = CloudRegionRepository(db)

    def sync_regions(self, provider_code: str) -> List[CloudRegion]:
        """
        同步云厂商的区域列表，并返回数据库中的最新数据
        :param provider_code: 云厂商编码（aliyun、tencentcloud、huawei 等）
        """

        existing_region = self.list_regions(provider_code)
        if existing_region:
            logger.info(f"[{provider_code}] 区域已存在数据库，无需同步")
            return existing_region

        # 1️⃣ 读取云厂商配置
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client = CloudClientFactory.create_client(
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        # 3️⃣ 调用客户端方法获取区域列表
        if provider_code == "aliyun":
            regions = client.list_regions(provider_code)
        # elif provider_code == "tencentcloud":
        #     regions = client.list_regions()
        else:
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND,
                message=Message.CLOUD_PROVIDER_NOT_FOUND
            )

        # 4️⃣ 批量插入或更新数据库
        self.region_repo.bulk_upsert(provider_code, regions)

        # 5️⃣ 查询数据库中最新的数据返回
        db_regions = self.list_regions(provider_code)
        logger.info(f"[{provider_code}] 共同步 {len(db_regions)} 个 Region")
        return db_regions


    def list_regions(self, provider_code: str) -> List[CloudRegion]:
        """仅从数据库获取（不发云厂商API）"""
        return self.region_repo.get_by_provider(provider_code)
