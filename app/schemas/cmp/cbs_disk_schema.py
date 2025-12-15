from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TagItem(BaseModel):
    title: Optional[str]
    sub_title: Optional[str]


class CbsDiskBase(BaseModel):
    disk_id: str

    cloud_provider_code: str
    region_id: str
    zone_id: str
    resource_group_id: int

    disk_type: str
    disk_category: str
    disk_size: int

    iops_level: Optional[str] = None

    encrypted: bool = False
    encryption_key_id: Optional[str] = None

    charge_type: str
    period: Optional[int]
    expired_time: Optional[datetime] = None
    auto_renew: bool = False

    attached_instance_id: Optional[str]
    attached_device: Optional[str] = None
    attached_time: Optional[datetime] = None
    detached_time: Optional[datetime] = None

    snapshot_count: int = 0
    last_snapshot_time: Optional[datetime] = None
    tags: Optional[List[TagItem]] = []
    description: Optional[str] = None

class CbsDiskCreate(CbsDiskBase):
    pass

class CbsDiskOut(CbsDiskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CbsDiskPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CbsDiskOut]


class CbsDiskReleaseSchema(BaseModel):
    cbs_id: int