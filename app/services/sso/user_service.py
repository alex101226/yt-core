from sqlalchemy.orm import Session

from app.repositories.sso.user_repo import UserRepository

from app.schemas.sso.auth_schema import UserRegister

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)


    def user_info(self, user_id: int) -> UserRegister:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        return user