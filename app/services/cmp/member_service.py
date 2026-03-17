from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.cmp.member_repo import MemberRepository
from app.repositories.sso.user_repo import UserRepository
from app.schemas.cmp.member_schema import MemberCreateSchema, MemberPageSchema, MemberOutSchema


class MemberService:
    def __init__(self, sso_db: Session, cmp_db: Session):
        self.sso_db = sso_db
        self.cmp_db = cmp_db
        self.repo = MemberRepository(cmp_db)
        self.user_repo = UserRepository(sso_db)

    def member_create(self, data: MemberCreateSchema, operator: dict):
        user = self.user_repo.get_by_username(data.member_account)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        exists = self.repo.get_by_user_id(user.id)
        if exists:
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message="该账号已是会员")

        payload = {
            **data.model_dump(),
            "user_id": user.id,
            "created_by": operator.get("user_id"),
            "created_by_name": operator.get("username"),
        }

        try:
            self.repo.create(payload)
            self.cmp_db.commit()
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def member_page_list(self, page: int, page_size: int, member_name: str = None, member_account: str = None, member_type: str = None):
        items, total = self.repo.page_list(page, page_size, member_name, member_account, member_type)
        return MemberPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[MemberOutSchema.model_validate(item) for item in items],
        )

    def member_list(self):
        items = self.repo.list_all()
        return [MemberOutSchema.model_validate(item) for item in items]

    def member_detail(self, member_id: int):
        member = self.repo.get_by_id(member_id)
        if not member:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return member

    def member_delete(self, member_id: int):
        member = self.repo.get_by_id(member_id)
        if not member:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        try:
            self.repo.delete(member)
            self.cmp_db.commit()
            return True
        except Exception:
            self.cmp_db.rollback()
            raise

    def member_toggle_freeze(self, member_id: int):
        member = self.repo.get_by_id(member_id)
        if not member:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        try:
            is_frozen = self.repo.toggle_freeze(member)
            self.cmp_db.commit()
            return {"is_frozen": is_frozen}
        except Exception:
            self.cmp_db.rollback()
            raise
