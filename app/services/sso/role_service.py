from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.sso.role_repo import RoleRepository

from app.schemas.sso.role_schema import RoleAddSchema

class RoleService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = RoleRepository(db)

    def role_create(self, data: RoleAddSchema):
        result = self.repo.role_create(**data.model_dump())
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message="创建失败")
        return result

    def role_list(self):
        return self.repo.role_list()
