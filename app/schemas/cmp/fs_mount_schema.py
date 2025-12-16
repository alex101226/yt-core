from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class FileSystemMountBase(BaseModel):
    cloud_provider_code: str
    region_id: str
    zone_id: str
    vpc_id: int
    subnet_id: int
    mount_alias: str
    fs_type: str
    fs_id: int

class FileSystemMountCreate(FileSystemMountBase):
    security_group_id: int
    pass

class FileSystemMountOut(FileSystemMountBase):
    id: int
    mount_id: str = None
    mount_name: str = None
    domain_name: Optional[str] = None
    security_group_id: Optional[int] = 0
    security_group_name: Optional[str] = None
    vpc_name: Optional[str] = None
    subnet_name: Optional[str] = None
    fs_name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileSystemMountPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[FileSystemMountOut]