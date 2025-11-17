# app/schemas/public/cloud_zone_schema.py

from datetime import datetime
from pydantic import BaseModel, Field


class CloudZoneBase(BaseModel):
    id: int
    provider_code: str
    region_id: str
    zone_id: str
    zone_name: str
    created_at: datetime
    updated_at: datetime

class CloudZoneOut(CloudZoneBase):
    class Config:
        orm_mode = True
