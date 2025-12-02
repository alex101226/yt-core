from typing import List, Optional
from sqlalchemy.orm import Session

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate

from app.repositories.cmp.eip_repo import EipRepository

class EIPService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EipRepository(db)

    def create_eip(self, user_id: int, data: EIPCreate):
        result = self.repo.create_eip(user_id, data)
        return result