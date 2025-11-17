from pydantic import BaseModel
from typing import Optional, List


class ResourceGroupBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class ResourceGroupCreate(ResourceGroupBase):
    pass


class ResourceGroupUpdate(BaseModel):
    name: Optional[str] = None
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