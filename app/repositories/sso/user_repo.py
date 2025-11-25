from typing import Optional

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, load_only
from app.models.sso.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    #   根据username查找
    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter_by(username = username).first()

    #   根据id查找
    def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                load_only(User.id, User.username, User.email, User.nickname, User.mobile)
            )
            .where(User.id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()


    def get_by_email_or_mobile(self, email: EmailStr, mobile: str = None) -> Optional[User]:
        conditions = []

        if email:
            conditions.append(User.email == email)
        if mobile:
            conditions.append(User.mobile == mobile)

        if not conditions:
            return None  # 没有条件直接返回

        return self.db.query(User).filter(or_(*conditions)).first()

    #   创建
    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user