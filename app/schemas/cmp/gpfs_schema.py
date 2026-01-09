from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class GPFSSchema(BaseModel):
    cloud_provider_code: str
    region_id: str
    zone_id: str
    resource_group_id: int

    vpc_id: Optional[str]
    subnet_id: Optional[str]
    charge_type: Optional[str]

    storage_type: str
    capacity_gb: int

    fs_alias: str
    description: Optional[str]

class GPFSCreate(GPFSSchema):
    price: float = 0
    pass

class GPFSOut(GPFSSchema):
    id: int
    fs_id: str
    fs_name: str
    status: str
    used_capacity_gb: int
    price: Optional[float] = 0.00
    created_by: int = 0
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        from_attributes = True

class GPFSPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[GPFSOut]