# app/services/public/cloud_provider_service.py

from sqlalchemy.orm import Session

from app.repositories.public.cloud_provider_repo import CloudProviderRepository
from app.models.public.cloud_provider import CloudCredentialsPlatform
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message


class CloudProviderService:

    def __init__(self, db: Session):
        self.db = db
        self.provider_repo = CloudProviderRepository(db)

    def create_provider(self, **kwargs) -> CloudCredentialsPlatform:
        # provider_code 唯一性校验
        if self.provider_repo.get_by_code(kwargs.get("provider_code")):
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_EXISTS,
                message=Message.CLOUD_PROVIDER_EXISTS
            )
        return self.provider_repo.create(**kwargs)

    def update_provider(self, record_id: int, **kwargs):
        if not self.provider_repo.get_by_id(record_id):
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_NOT_FOUND,
                message=Message.CLOUD_PROVIDER_NOT_FOUND
            )
        return self.provider_repo.update(record_id, **kwargs)

    def delete_provider(self, record_id: int) -> bool:
        success = self.provider_repo.delete(record_id)
        if not success:
            raise BusinessException(
                code=ErrorCode.CLOUD_PROVIDER_DELETE_FAILED,
                message=Message.CLOUD_PROVIDER_DELETE_FAILED
            )
        return True

    def list_providers(self, page: int, page_size: int):
        return self.provider_repo.list_page(page, page_size)
