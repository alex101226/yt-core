from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.sso.role_repo import RoleRepository

from app.schemas.sso.role_schema import RoleAddSchema, RolePageSchema, RoleOutSchema, RoleUpdateSchema

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

    def role_update(self, data: RoleUpdateSchema):
        role = self.repo.role_get_by_id(data.role_id)
        if not role:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        result = self.repo.role_update(
            role,
            {
                "role_name": data.role_name,
                "description": data.description,
            }
        )
        self.db.commit()
        return result

    def role_page_list(self, page: int, page_size: int, role_name: str = None):
        items, total = self.repo.role_page_list(page, page_size, role_name)
        return RolePageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[RoleOutSchema.model_validate(item) for item in items],
        )

    def role_delete(self, role_id: int, fallback_role_code: str = "admin"):
        role = self.repo.role_get_by_id(role_id)
        if not role:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if role.role_code in {"root", fallback_role_code}:
            raise BusinessException(code=ErrorCode.PERMISSION_DENIED, message="该角色不可删除")

        fallback = self.repo.role_get_by_code(fallback_role_code)
        if not fallback:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message="默认降级角色不存在")

        try:
            if self.repo.role_user_count(role.role_code) > 0:
                self.repo.role_downgrade_users(role.role_code, fallback_role_code)
            self.repo.role_delete(role)
            self.db.commit()
            return True
        except BusinessException:
            self.db.rollback()
            raise
        except Exception:
            self.db.rollback()
            raise
