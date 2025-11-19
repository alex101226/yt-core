from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SecurityGroupSearch(BaseModel):
    cloud_provider_code: Optional[str] = Field(None, description="云厂商 code")
    region_id: Optional[str] = Field(None, description="区域 ID")
    resource_group_id: Optional[int] = Field(None, description="资源组 ID")
    security_name: Optional[str] = Field(None, description="安全组名称，模糊匹配")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=200, description="每页数量")

class SecurityGroupOut(BaseModel):
    id: str
    cloud_group_id: Optional[str]
    security_name: str
    description: Optional[str]
    cloud_provider_code: str
    cloud_certificate_id: int
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
    security_name: str
    description: Optional[str] = None
    cloud_provider_code: str
    cloud_certificate_id: int
    region_id: str
    vpc_id: int

