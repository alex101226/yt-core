from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ContainerImageSchema(BaseModel):
    cloud_provider_code: str
    region_id: str
    resource_group_id: Optional[int]

    repository_name: str
    charge_type: str
    # capacity_gb: int


class ContainerImageCreate(ContainerImageSchema):
    pass


class ContainerImageOut(ContainerImageSchema):
    id: int
    repository_id: str
    description: Optional[str] = None
    namespace_count: Optional[int] = 0
    capacity_gb: Optional[int] = 0
    used_capacity_gb: Optional[int] = 0
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ContainerImagePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ContainerImageOut]