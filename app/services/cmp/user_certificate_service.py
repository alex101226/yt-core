from sqlalchemy.orm import Session

from app.repositories.cmp.user_certificate_repo import UserCertificateRepository

from app.schemas.cmp.user_certificate_schema import UserCertificateList
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

class UserCertificateService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserCertificateRepository(db)

    def create_certificate(self, data: dict):
        user_id = data["user_id"]
        count = self.repo.count_by_user(user_id)

        # 如果是第一条，自动设为默认
        if count == 0:
            data["is_default"] = 1
        else:
            data["is_default"] = 0

        # cloud_code 唯一校验
        if self.repo.get_by_code(data['cloud_code']):
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message=Message.DATA_DUPLICATE)
        return self.repo.create(data)

    def get_certificate(self, record_id: int):
        obj = self.repo.get_by_id(record_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    # 下拉选择的list
    def certificate_list(self, user_id: int):
        result = self.repo.certificate_list(user_id)
        out_result = [UserCertificateList.model_validate(i) for i in result]
        return out_result

    # 分页查找
    def certificates_page_list(self, page: int, page_size: int):
        return self.repo.list_page(page, page_size)

    def update_certificate(self, record_id: int, **kwargs):
        obj = self.repo.update(record_id, **kwargs)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj

    def delete_certificate(self, record_id: int) -> bool:
        ok = self.repo.delete(record_id)
        if not ok:
            raise BusinessException(code=ErrorCode.DATABASE_ERROR, message=Message.DATABASE_ERROR)
        return True

    # 设置默认云凭证
    def set_default_certificate(self, user_id: int, record_id: int):
        # 清除旧默认
        self.repo.clear_default(user_id)

        # 设置新默认
        obj = self.repo.set_default(record_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="凭证不存在")

        return {
            "id": obj.id,
            "is_default": obj.is_default,
            "updated_at": obj.updated_at,
            "cloud_code": obj.cloud_code,
        }

    # 返回用户的默认凭证
    def get_default_certificate(self, user_id: int):
        obj = self.repo.get_certificate_find(user_id)
        return obj

    def get_user_ak(self, user_id: int):
        obj = self.repo.get_user_ak(user_id)
        if not obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return obj