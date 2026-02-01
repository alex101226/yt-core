from typing import Optional

from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.models.sso.user import User


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


    def get_by_email(self, email: EmailStr) -> Optional[User]:
        find = self.db.query(User).filter(User.email == email).first()
        if not find:
            return None
        return find

    #   创建
    def create(self, user: dict) -> User:
        register_db = User(**user)
        self.db.add(register_db)
        # self.db.flush()
        return register_db

    # 获取用户列表
    def user_page_list(self, page: int, page_size: int, nickname: str, username: str):
        query = self.db.query(
            User.id,
            User.nickname,
            User.username,
            User.email
        ).order_by(User.id.desc())

        filters = []
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

        self.db.delete(find)
        self.db.commit()
        return True