from typing import Optional

from sqlalchemy.orm import Session

from app.models.sso.user import User
from app.models.sso.role import Role


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    #   根据username查找
    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter_by(username = username).first()

    #   根据id查找
    def get_by_id(self, user_id: int) -> Optional[User]:
        find = self.db.query(User).filter_by(id = user_id).first()
        return find

    def user_info(self, user_id: int):
        find = self.db.query(
            User,
            Role.role_name.label("role_name"),
        ).outerjoin(Role, Role.role_code == User.role_code).filter(User.id == user_id, User.is_released == 0).first()
        if not find:
            return None
        return find

    #   创建
    def create(self, user: dict) -> User:
        register_db = User(**user)
        self.db.add(register_db)
        self.db.flush()
        return register_db

    # 获取用户列表
    def user_page_list(
        self,
        page: int,
        page_size: int,
        nickname: str,
        username: str,
        parent_id: int = None,
        only_user_type: str = None,
    ):
        query = self.db.query(
            User.id,
            User.nickname,
            User.username,
            User.parent_id,
            User.created_at,
            User.updated_at,
            User.user_type,
        ).order_by(User.id.desc())

        filters = [User.is_released == 0]
        if parent_id is not None:
            filters.append((User.id == parent_id) | (User.parent_id == parent_id))
        if only_user_type:
            filters.append(User.user_type == only_user_type)
        if nickname:
            filters.append(User.nickname.like(f"%{nickname}%"))
        if username:
            filters.append(User.username.like("%" + username + "%"))

        if filters:
            query = query.filter(*filters)

        total = query.count()
        offset_value = (page - 1) * page_size
        items = query.offset(offset_value).limit(page_size).all()

        return items, total

    # 删除账户
    def user_delete(self, user_id: int):
        find = self.get_by_id(user_id)

        if not find:
            return None

        find.is_released = True
        self.db.commit()
        return True

    #   返回自己和自己下属的id
    def get_parent_id(self, parent_id: int) -> Optional[int]:
        return self.db.query(User).filter(
            (User.id == parent_id) | (User.parent_id == parent_id)
        ).all()

    # 返回用户数量和用户的角色数量
    def user_count(self, user: dict):
        parent_id = user.get('parent_id')
        user_id = user.get('user_id')
        # 普通用户：只有自己
        if parent_id != 0:
            return {
                "user_count": 1,
                "user_role": 1,
            }

        sub_count =  self.db.query(User).filter(User.parent_id == user_id).count()
        return {
            "user_count": sub_count + 1,
            "user_role": 1,
        }

    # 修改用户
    def save_user(self, data: dict):
        user = self.get_by_id(data['user_id'])
        if not user:
            return None
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def save_password(self, data: dict):
        user = self.get_by_id(data['user_id'])
        if not user:
            return None
        user.hashed_password = data['hashed_password']
        self.db.commit()
        self.db.refresh(user)
        return user

    # 管理员列表（用于外部过滤未绑定会员）
    def admin_user_list(self, exclude_user_ids=None):
        query = (
            self.db.query(
                User.id,
                User.nickname,
                User.username,
                User.parent_id,
                User.created_at,
                User.updated_at,
                User.user_type,
            )
            .filter(
                User.is_released == 0,
                User.role_code == "admin",
            )
            .order_by(User.id.desc())
        )
        if exclude_user_ids:
            query = query.filter(~User.id.in_(exclude_user_ids))
        return query.all()
