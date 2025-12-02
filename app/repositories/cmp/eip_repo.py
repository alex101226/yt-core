from typing import Optional
from sqlalchemy.orm import Session
from app.models.cmp.eip import Eip
from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate

# eip的repository
class EipRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建eip
    def create_eip(self, user_id, data: EIPCreate):
        item = data.model_dump()
        item['user_id'] = user_id

        obj = Eip(**item)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return True