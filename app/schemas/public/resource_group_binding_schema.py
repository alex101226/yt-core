from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ResourceGroupBindingBase(BaseModel):
    resource_group_id: int = Field(..., description="资源组 ID")
    resource_type: str = Field(..., description="资源类型")
    resource_id: str = Field(..., description="资源唯一 ID")


class ResourceGroupBindingCreate(ResourceGroupBindingBase):
    pass


class ResourceGroupBindingOut(ResourceGroupBindingBase):
    id: int
    resource_group_id: int
    resource_type: str
    resource_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceGroupBindingPage(BaseModel):
    page: int
    pageSize: int
    total: int
    items: List[ResourceGroupBindingOut]
