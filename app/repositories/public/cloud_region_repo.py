# app/repositories/public/cloud_region_repository.py
from sqlalchemy.orm import Session
from typing import List
from app.models.public.cloud_region import CloudRegion
from datetime import datetime

class CloudRegionRepository:
    """区域表数据操作"""

    def __init__(self, db: Session):
        self.db = db

    """
    批量插入或更新区域数据
    :param provider_code: 云厂商编码
    :param regions: [{'region_id': 'cn-hangzhou', 'region_name': '华东1（杭州）'}, ...]
    """
    def bulk_upsert(self, provider_code: str, regions: List[dict]):

        now = datetime.now()

        for r in regions:
            existing = (
                self.db.query(CloudRegion)
                .filter(
                    CloudRegion.provider_code == provider_code, # type: ignore
                    CloudRegion.region_id == r["region_id"],    # type: ignore
                )
                .first()
            )
            if existing:
                existing.region_name = r["region_name"]
                existing.updated_at = now
            else:
                self.db.add(
                    CloudRegion(
                        provider_code=provider_code,
                        region_id=r["region_id"],
                        region_name=r["region_name"],
                        created_at=now,
                        updated_at=now,
                    )
                )
        self.db.commit()

    """获取指定云厂商的所有区域"""
    def get_by_provider(self, provider_code: str) -> List[CloudRegion]:
        return (
            self.db.query(CloudRegion)
            .filter(CloudRegion.provider_code == provider_code)   # type: ignore
            .order_by(CloudRegion.region_id)
            .all()
        )
