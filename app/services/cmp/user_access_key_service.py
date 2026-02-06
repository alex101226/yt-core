from sqlalchemy.orm import Session
from nanoid import generate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode
from app.services.cmp.operation_helper import execute_with_notification

from app.repositories.cmp.user_access_key_repo import UserAccessKeyRepo
from app.schemas.cmp.user_access_key_schema import CreateUserAccessKeySchema

def generate_access_key_secret(size: int):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return generate(alphabet, size)

class UserAccessKeyService:
    def __init__(self, session: Session):
        self._session = session
        self._repo = UserAccessKeyRepo(session)

    # 创建key
    def create_access_key(self, user: dict, data: CreateUserAccessKeySchema):
        user_id = user.get('user_id')
        username = user.get('username')
        payload = {
            "created_by": user_id,
            "created_by_name": username,
            "cloud_provider_code": data.cloud_provider_code,
            "access_key_id": "AKID" + generate_access_key_secret(32),
            "access_key_secret": "AKSC" + generate_access_key_secret(40),
            "status": True,
        }
        result = self._repo.create_access_key(payload)
        return result


    # 列表
    def access_key_page_list(self, parent_id: int, page: int, page_size: int):
        total, items = self._repo.get_access_key_page_list(parent_id, page, page_size)
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }

    # 禁用
    def set_disabled(self, access_key_id: int):
        result = self._repo.set_disabled(access_key_id)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return result

    # 删除
    def release(self, access_key_id: int):
        result = self._repo.set_release(access_key_id)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return result