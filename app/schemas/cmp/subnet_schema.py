# app/schemas/cmp/subnet.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class SubnetBase(BaseModel):
    subnet_name: str = Field(..., description="子网名称")
    description: Optional[str] = Field(None, description="子网描述信息")
    vpc_id: int = Field(..., description="所属 VPC ID")
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    cloud_provider_code: str = Field(..., description="云厂商 code")
    cloud_certificate_id: int = Field(..., description="云凭证ID")
    region_id: str = Field(..., description="区域 ID")
    zone_id: Optional[str] = Field(None, description="可用区 ID")
    cidr_block: str = Field(..., description="子网网段，例如 192.168.1.0/24")

class SubnetCreate(SubnetBase):
    pass

class SubnetUpdate(BaseModel):
    subnet_name: Optional[str] = Field(None, description="子网名称")
    description: Optional[str] = Field(None, description="子网描述信息")
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    zone_id: Optional[str] = Field(None, description="可用区 ID")
    cidr_block: Optional[str] = Field(None, description="子网网段")
    is_released: Optional[bool] = Field(None, description="是否已释放")
    released_at: Optional[datetime] = Field(None, description="释放时间 (UTC)")

class SubnetOut(SubnetBase):
    id: int
    subnet_id: str = Field(..., description="云厂商原始子网 ID")
    is_released: bool
    released_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubnetPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[SubnetOut]
