from typing import Optional, List, Tuple, Any
from sqlalchemy.orm import Session
from app.models.public.resource_group import ResourceGroup

class ResourceGroupRepository:
    """资源组仓储层"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, data: dict) -> ResourceGroup:
        obj = ResourceGroup(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, record_id: int) -> Optional[ResourceGroup]:
        return self.db.query(ResourceGroup).get(record_id)

    def get_by_code(self, code: str) -> Optional[ResourceGroup]:
        return self.db.query(ResourceGroup).filter_by(code = code).first()

    def list_page(self, page: int, page_size: int) -> tuple[int, list[type[ResourceGroup]]]:
        query = self.db.query(ResourceGroup).order_by(ResourceGroup.id.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    def update(self, record_id: int, data: dict) -> Optional[ResourceGroup]:
        obj = self.get_by_id(record_id)
        if not obj:
            return None
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, record_id: int) -> bool:
        obj = self.get_by_id(record_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True
