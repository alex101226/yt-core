from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class EIPSchema(BaseModel):
    resource_group_id: Optional[int]
    cloud_provider_code: str
    region_id: str
    zone_id: str
    description: Optional[str]
    eip_name: str
    internet_charge_type: str
    bandwidth: int



class EIPCreate(EIPSchema):
    price: float
    pass

class EIPOut(EIPSchema):
    id: int
    public_ip: Optional[str]
    bind_instance_id: Optional[str]
    status: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    resource_group_name: Optional[str]
    sync_status: Optional[int]

    class Config:
        from_attributes = True

class EIPPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[EIPOut]


class EIPSave(BaseModel):
    eip_id: int
    status: str