from sqlalchemy.orm import Session

from app.repositories.sso.user_repo import UserRepository
from app.schemas.sso.auth_schema import UserOutSchema, UserPageSchema

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def user_info(self, user_id: int) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "nickname": user.nickname,
        }

    # 用户列表
    def user_page_list(self, page: int, page_size: int, nickname: str, username: str):
        items, total = self.user_repo.user_page_list(page, page_size, nickname, username)
        return UserPageSchema(
            page = page,
            page_size = page_size,
            total = total,
            items = [UserOutSchema.model_validate(item) for item in items],
        )

    # 删除用户
    def user_delete(self, user_id: int) -> dict:
        result = self.user_repo.user_delete(user_id)
        if not result:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        return result
