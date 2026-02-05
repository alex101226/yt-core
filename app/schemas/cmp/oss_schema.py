from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class TagItem(BaseModel):
    title: Optional[str]
    sub_title: Optional[str]

class OssBase(BaseModel):
    bucket_name: str = None
    cloud_provider_code: str = None
    region_id: str = None
    resource_group_id: Optional[int] = 0
    description: Optional[str] = None
    storage_class: Optional[str] = None
    permission: Optional[str] = None
    # public_url: Optional[str] = None


class OssCreate(OssBase):
    price: float = 0
    pass

class OssOut(OssBase):
    id: int = 0
    bucket_id: str = None
    status: str = None
    charge_type: str = None
    used_size_bytes: int = 0
    user_id: int = 0
    created_at: datetime = None
    updated_at: datetime = None
    resource_group_name: str = None
    object_count: int = 0

    class Config:
        from_attributes = True

class OssPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[OssOut]
