from typing import List
from sqlalchemy.orm import Session

from app.repositories.public.cloud_zone_repo import CloudZoneRepository
from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode

from app.schemas.public.cloud_zone_schema import CloudZoneList
from app.services.public.cloud_service import CloudService


class CloudZoneService:
    """云可用区服务层"""

    def __init__(self, db: Session):
        self.db = db
        self.zone_repo = CloudZoneRepository(db)
        self.provider_repo = CloudProviderRepository(db)

    #   同步指定区域的可用区列表，并返回数据库中最新数据
    def sync_zones(self, provider_code: str, region_id: str) -> List[CloudZoneList]:
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )
        client_zone = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )
        zones = client_zone.list_zones(provider_code, region_id)
        return zones

    def list_zones(self, provider_code: str, region_id: str) -> List[CloudZoneList]:
        return self.zone_repo.get_by_zones(provider_code, region_id)