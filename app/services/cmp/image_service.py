from sqlalchemy.orm import Session

from app.repositories.public.cloud_provider_repo import CloudProviderRepository

from app.services.public.cloud_service import CloudService
class ImageService:
    def __init__(self, db: Session):
        self.db = db
        self.provider_repo = CloudProviderRepository(db)

    def list(self, provider_code: str, region_id: str):
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

        images = client_region.list_images(region_id)
        return images
