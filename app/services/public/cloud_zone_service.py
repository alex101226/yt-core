from typing import List
from sqlalchemy.orm import Session

from app.clients.cloud_client_factory import CloudClientFactory
from app.models.public.cloud_zone import CloudZone
from app.repositories.public.cloud_zone_repo import CloudZoneRepository
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.core.logger import logger


class CloudZoneService:
    """云可用区服务层"""

    def __init__(self, db: Session):
        self.db = db
        self.zone_repo = CloudZoneRepository(db)
        self.provider_repo = CloudProviderRepository(db)

    def sync_zones(self, provider_code: str, region_id: str) -> List[CloudZone]:
        """
        同步指定区域的可用区列表，并返回数据库中最新数据
        :param provider_code: 云厂商编码
        :param region_id: 区域编码
        """
        # 1️⃣ 查询数据库是否已有可用区数据
        existing_zones = self.list_zones(provider_code, region_id)
        if existing_zones:
            logger.info(f"[{provider_code}][{region_id}] 可用区已存在数据库，无需同步")
            return existing_zones

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

        # 3️⃣ 调用客户端方法获取可用区列表
        if provider_code == "aliyun":
            zones = client.list_zones(region_id)
        # elif provider_code == "tencentcloud":
        #     zones = client.list_zones(region_id)
        else:
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND,
                message=Message.CLOUD_PROVIDER_NOT_FOUND
            )

        # 4️⃣ 批量插入或更新数据库
        self.zone_repo.bulk_upsert(provider_code, region_id, zones)

        # 5️⃣ 查询数据库最新数据返回
        db_zones = self.list_zones(provider_code, region_id)
        logger.info(f"[{provider_code}][{region_id}] 同步 {len(db_zones)} 个可用区")
        return db_zones

    def list_zones(self, provider_code: str, region_id: str) -> List[CloudZone]:
        return self.zone_repo.get_by_zones(provider_code, region_id)