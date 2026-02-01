from typing import Optional

from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.core.logger import logger
from app.models.sso.role import Role

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def role_create(self, **data):
        role_db = Role(**data)
        self.db.add(role_db)
        self.db.commit()
        self.db.refresh(role_db)
        return role_db

    def role_list(self):
        roles = self.db.query(Role).all()
        return roles