from typing import Optional

from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.models.sso.user import User


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    #   根据username查找
    def get_by_username(self, username: str) -> User:
        return self.db.query(User).filter(User.username == username).first()

    #   根据id查找
    def get_by_id(self, user_id: int) -> User:
        return self.db.query(User).filter(User.id == user_id).first()


    def get_by_email_or_mobile(self, email: EmailStr, mobile: str = None) -> Optional[type[User]]:
        query = self.db.query(User)
        if email:
            query = query.filter(User.email == email)
        if mobile:
            query = query.filter(User.mobile == mobile)
        return query.first()

    #   创建
    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user