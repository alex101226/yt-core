from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List


class ResourceGroupBase(BaseModel):
    rg_name: str
    rg_code: str
    description: str

class ResourceGroupCreate(ResourceGroupBase):
    pass


class ResourceGroupUpdate(BaseModel):
    rg_name: Optional[str] = None
    description: Optional[str] = None


class ResourceGroupOut(ResourceGroupBase):
    id: int

    class Config:
        from_attributes = True


class ResourceGroupPage(BaseModel):
    page: int
    pageSize: int
    total: int
    items: List[ResourceGroupOut]




class ResourceGroupBindingBase(BaseModel):
    resource_group_id: int
    resource_type: str
    resource_id: str


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
