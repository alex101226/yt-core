from typing import Optional

from pydantic import EmailStr
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, load_only

from app.core.logger import logger
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