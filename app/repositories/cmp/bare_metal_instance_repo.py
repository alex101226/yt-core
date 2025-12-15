from datetime import datetime, timezone
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.bare_metal_instance import BareMetalInstance
from app.repositories.cmp.server_instance_repo import ServerInstanceRepo


class BareMetalInstanceRepo:
    def __init__(self, db: Session):
        self.db = db

    # 创建裸金属
    def bare_metal_create(self, data: dict) -> int:
        instance = BareMetalInstance(**data)
        self.db.add(instance)
        self.db.flush()
        self.db.commit()
        return instance.id
