from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class CephfsBase(BaseModel):
    fs_name: str = Field(...)
    description: Optional[str] = None
    cloud_provider_code: str = Field(...)
    region_id: str = Field(...)
    resource_group_id: Optional[int] = Field(...)
    storage_type: str = Field(...)
    capacity_gb: int = Field(...)

class CephfsCreate(CephfsBase):
    price: float = Field(...)
    pass

class CephfsOut(CephfsBase):
    id: int = 0
    fs_id: str = None
    status: str = None
    charge_type: str = None
    used_size_gb: int = 0
    # user_id: int = 0
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        from_attributes = True

class CephfsPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[CephfsOut]


# 容量配置
class CEPHFSCapacitySchema(BaseModel):
    cephfs_id: int
    capacity_gb: str