from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.public.cloud_certificate import CloudCertificate

class CloudCertificateRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> CloudCertificate:
        obj = CloudCertificate(**kwargs)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, record_id: int) -> Optional[CloudCertificate]:
        return self.db.get(CloudCertificate, record_id)

    def get_by_code(self, cloud_code: str) -> Optional[CloudCertificate]:
        return self.db.query(CloudCertificate).filter_by(cloud_code=cloud_code).first()

    def list_page(self, page: int, page_size: int) -> Tuple[int, List[CloudCertificate]]:
        q = self.db.query(CloudCertificate).order_by(CloudCertificate.id.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    def update(self, record_id: int, **kwargs) -> Optional[CloudCertificate]:
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
