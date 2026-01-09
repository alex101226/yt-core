from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CbsDiskBase(BaseModel):
    cloud_provider_code: str
    region_id: str
    zone_id: str
    resource_group_id: int

    disk_name: Optional[str] = None
    disk_type: str
    disk_category: str
    disk_size: int

    charge_type: str
    period: Optional[int] = 1
    auto_renew: bool = False

    attached_instance_id: Optional[str] = None
    attached_device: Optional[str] = None
    attached_time: Optional[datetime] = None

    tags: Optional[List[str]] = []
    description: Optional[str] = None

class CbsDiskCreate(CbsDiskBase):
    price: Optional[float] = None
    pass

class CbsDiskOut(CbsDiskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    status: Optional[str] = None
    resource_group_name: Optional[str] = None

    class Config:
        from_attributes = True

class CbsDiskPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CbsDiskOut]


class CbsDiskReleaseSchema(BaseModel):
    cbs_id: int