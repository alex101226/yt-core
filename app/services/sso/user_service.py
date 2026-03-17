from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.core.security import hash_password
from app.core.logger import logger

from app.repositories.sso.user_repo import UserRepository
from app.schemas.sso.auth_schema import (
UserOutSchema, UserPageSchema, UserRegister, UpdateUserSchema, UpdateUserPasswordSchema
)

from app.services.cmp.account_service import AccountService
from app.repositories.cmp.member_repo import MemberRepository

class UserService:
    def __init__(self, db: Session, cmp_db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.account_service = AccountService(cmp_db)
        self.cmp_db = cmp_db
        self.member_repo = MemberRepository(cmp_db)

    # 获取用户信息
    def user_info(self, user_id: int):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        result = self.user_repo.user_info(user_id)
        if not result:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
        user, role_name = result

        account_by_id = user.id if user.parent_id == 0 else user.parent_id
        account = self.account_service.account_exists(account_by_id)

        return {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "role_code": user.role_code,
            "role_name": role_name,
            "balance": account.balance if account else 0,
            "parent_id": user.id if user.parent_id == 0 else user.parent_id,
            "account_name": account.account_name if account else None,
            "account_type": account.account_type if account else None,
            "account_status": account.account_status if account else None,
        }

    # 用户列表
    def user_page_list(self, current_user: dict, page: int, page_size: int, nickname: str, username: str):
        user_id = current_user.get("user_id")
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        parent_id = None
        only_user_type = None
        if user.user_type != "internal":
            parent_id = user.parent_id or 0
            if parent_id == 0:
                parent_id = user.id
        else:
            only_user_type = "tenant"

        items, total = self.user_repo.user_page_list(page, page_size, nickname, username, parent_id, only_user_type)
        return UserPageSchema(
            page = page,
            page_size = page_size,
            total = total,
            items = [UserOutSchema.model_validate(item) for item in items],
        )

    # 创建用户
    def user_create(self, user_id: int, data: UserRegister):
        # 检查重复
        exists = self.user_repo.get_by_username(data.username)

        if exists:
            raise BusinessException(code=ErrorCode.USER_ALREADY_EXISTS, message=Message.USER_ALREADY_EXISTS)

        role_code = data.role_code or "normal"
        payload = {
            "nickname": data.nickname,
            "username": data.username,
            "hashed_password": hash_password(data.password),
            "role_code": role_code,
            "parent_id": 0 if role_code == "root" else user_id,
            "user_type": "internal" if role_code == "root" else "tenant",
        }

        # 创建用户
        new_user = self.user_repo.create(payload)
        # self.account_service.account_create(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    # 删除用户
    def user_delete(self, user_id: int):
        try:
            with self.db.begin():
                user_result = self.user_repo.user_delete(user_id)
                if not user_result:
                    raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)
                self.account_service.account_delete(user_id)
            return True
        except BusinessException as exception:
            self.db.rollback()
            raise exception

    # 返回用户数量
    def user_count(self, user: dict):
        user = self.user_repo.user_count(user)
        return user

    def user_member_list(self, parent_id: int):
        users_list = self.user_repo.get_parent_id(parent_id)
        # 遍历，只返回特定字段
        result = []
        for u in users_list:
            result.append({
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "role_code": u.role_code,
                "parent_id": u.parent_id,
                "role_name": '所有者' if u.parent_id == 0 else '成员'

            })
        return result

    # 内部人员列表
    def internal_user_page_list(self, page: int, page_size: int, nickname: str, username: str):
        items, total = self.user_repo.user_page_list(page, page_size, nickname, username, None, "internal")
        return UserPageSchema(
            page=page,
            page_size=page_size,
            total=total,
            items=[UserOutSchema.model_validate(item) for item in items],
        )

    # 管理员列表（未绑定会员，不分页）
    def admin_unbound_member_list(self):
        bound_user_ids = self.member_repo.active_member_user_ids()
        items = self.user_repo.admin_user_list(bound_user_ids)
        return [UserOutSchema.model_validate(item) for item in items]

    # 修改用户
    def save_user(self, user_id: int, data: UpdateUserSchema):
        payload = {
            'user_id': user_id,
            **data.model_dump(),
        }
        result = self.user_repo.save_user(payload)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message='修改失败')
        return result

    # 修改密码
    def save_password(self, user_id: int, data: UpdateUserPasswordSchema):
        payload = {
            'user_id': user_id,
            'hashed_password': hash_password(data.password),
        }
        result = self.user_repo.save_password(payload)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message='修改失败')
        return True
