from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SecurityGroup(BaseModel):
    sg_name: str
    # cloud_group_id: Optional[str]
    description: Optional[str]
    cloud_provider_code: str
    region_id: str
    vpc_id: int
    resource_group_id: Optional[int]

class SecurityGroupOut(BaseModel):
    id: int
    cloud_group_id: Optional[str]
    sg_id: str
    sg_name: str
    description: Optional[str]
    cloud_provider_code: str
    region_id: str
    vpc_id: int
    vpc_name: Optional[str] = None
    resource_group_id: Optional[int]
    resource_group_name: Optional[str] = None
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

class SecurityGroupCreate(SecurityGroup):
    pass

