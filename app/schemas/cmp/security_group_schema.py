from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SecurityGroup(BaseModel):
    id: str
    sg_id: str
    cloud_group_id: Optional[str]
    description: Optional[str]
    cloud_provider_code: str
    region_id: str
    vpc_id: int
    resource_group_id: Optional[int]

class SecurityGroupOut(BaseModel):
    id: str
    cloud_group_id: Optional[str]
    sg_id: str
    description: Optional[str]
    cloud_provider_code: str
    region_id: str
    vpc_id: int
    resource_group_id: Optional[int]
    sync_status: int
    is_released: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SecurityGroupPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SecurityGroupOut]

class SecurityGroupCreate(BaseModel):
    sg_id: str
    description: Optional[str] = None
    cloud_provider_code: str
    resource_group_id: Optional[int] = None
    region_id: str
    vpc_id: int

