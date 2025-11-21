# app/services/public/cloud_region_service.py
from typing import List
from sqlalchemy.orm import Session

from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.repositories.public.cloud_region_repo import CloudRegionRepository

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.schemas.public.cloud_region_schema import CloudRegionBase

from app.services.public.cloud_service import CloudService

class CloudRegionService:
    """云厂商区域同步与查询服务"""
    def __init__(self, db: Session):
        self.db = db
        self.provider_repo = CloudProviderRepository(db)
        self.region_repo = CloudRegionRepository(db)

    #    同步云厂商的区域列表，并返回数据库中的最新数据
    def sync_regions(self, provider_code: str) -> list[CloudRegionBase]:
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client_region = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        regions = client_region.list_regions()
        return regions


    def list_regions(self, provider_code: str) -> List[CloudRegionBase]:
        """仅从数据库获取（不发云厂商API）"""
        return self.region_repo.region_list(provider_code)
