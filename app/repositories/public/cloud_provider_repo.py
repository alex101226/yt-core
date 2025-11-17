# app/repositories/public/cloud_provider_repo.py
from typing import Optional
from sqlalchemy.orm import Session

from app.models.public.cloud_provider import CloudCredentialsPlatform


class CloudProviderRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> CloudCredentialsPlatform:
        obj = CloudCredentialsPlatform(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, provider_id: int) -> Optional[CloudCredentialsPlatform]:
        return self.db.query(CloudCredentialsPlatform).filter_by(id=provider_id).first()

    def get_by_code(self, provider_code: str) -> Optional[CloudCredentialsPlatform]:
        return self.db.query(CloudCredentialsPlatform).filter_by(provider_code=provider_code).first()

    def list_page(self, page: int, page_size: int):
        query = self.db.query(CloudCredentialsPlatform).order_by(CloudCredentialsPlatform.id.desc())
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    def update(self, record_id: int, **kwargs):
        obj = self.get_by_id(record_id)
        if not obj:
            return None
        for k, v in kwargs.items():
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
