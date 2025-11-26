from sqlalchemy.orm import Session

from app.repositories.public.cloud_provider_repo import CloudProviderRepository

from app.services.public.cloud_service import CloudService

class DiskTypeService:
    def __init__(self, db: Session):
        self.db = db
        self.provider_repo = CloudProviderRepository(db)

    def disk_type_list(self, provider_code: str, region_id: str, zone_id: str, instance_type_id: str, instance_charge_type: str):
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        images = client.list_disk_types(region_id, zone_id, instance_type_id, instance_charge_type.value)
        return images
