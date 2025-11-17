from typing import Tuple
from sqlalchemy.orm import Session

from app.repositories.public.cloud_certificate_repo import CloudCertificateRepository
from app.models.public.cloud_certificate import CloudCertificate
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

class CloudCertificateService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = CloudCertificateRepository(db)

    def create_certificate(self, **kwargs) -> CloudCertificate:
        # cloud_code 唯一校验
        if self.repo.get_by_code(kwargs.get("cloud_code")):
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message=Message.DATA_DUPLICATE)
        return self.repo.create(**kwargs)

    def get_certificate(self, record_id: int) -> CloudCertificate:
        obj = self.repo.get_by_id(record_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    def list_certificates(self, page: int, page_size: int) -> Tuple[int, list[CloudCertificate]]:
        return self.repo.list_page(page, page_size)

    def update_certificate(self, record_id: int, **kwargs) -> CloudCertificate:
        obj = self.repo.update(record_id, **kwargs)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    def delete_certificate(self, record_id: int) -> bool:
        ok = self.repo.delete(record_id)
        if not ok:
            raise BusinessException(code=ErrorCode.DATABASE_ERROR, message=Message.DATABASE_ERROR)
        return True
