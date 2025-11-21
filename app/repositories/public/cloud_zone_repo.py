# app/repositories/public/cloud_zone_repository.py
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.models.public.cloud_zone import CloudZone

class CloudZoneRepository:
    """可用区表数据操作"""

    def __init__(self, db: Session):
        self.db = db

    #   批量插入或更新可用区数据
    def bulk_upsert(self, provider_code: str, region_id: str, zones: List[dict]):

        now = datetime.now()

        for z in zones:
            existing = (
                self.db.query(CloudZone)
                .filter(
                    CloudZone.provider_code == provider_code,
                    CloudZone.region_id == region_id,
                    CloudZone.zone_id == z["zone_id"],
                )
                .first()
            )
            if existing:
                existing.zone_name = z["zone_name"]
                existing.updated_at = now
            else:
                self.db.add(
                    CloudZone(
                        provider_code=provider_code,
                        region_id=region_id,
                        zone_id=z["zone_id"],
                        zone_name=z["zone_name"],
                        created_at=now,
                        updated_at=now,
                    )
                )
        self.db.commit()

    #   获取指定云厂商和区域的所有可用区
    def get_by_zones(self, provider_code: str, region_id: str) -> List[CloudZone]:

        return (
            self.db.query(CloudZone)
            .filter(
                CloudZone.provider_code == provider_code,   # type: ignore
                CloudZone.region_id == region_id    # type: ignore
            )
            .order_by(CloudZone.zone_id)
            .all()
        )