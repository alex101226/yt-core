# app/schemas/cloud_provider_schema.py
from pydantic import BaseModel, Field
from typing import Optional, List

class CloudProviderBase(BaseModel):
    provider_code: str = Field(..., description="云厂商编码，例如 aliyun")
    provider_name: str = Field(..., description="云厂商名称")
    access_key_id: str = Field(..., description="AccessKey ID")
    access_key_secret: str = Field(..., description="AccessKey Secret（加密存储）")
    endpoint: str = Field(..., description="默认 Endpoint，例如 ecs.aliyuncs.com")
    description: Optional[str] = Field(None, description="描述信息")

class CloudProviderCreate(BaseModel):
    provider_code: Optional[str] = Field(None, description="云厂商唯一code")
    provider_name: Optional[str] = Field(None, description="云厂商名称")
    access_key_id: Optional[str] = Field(None, description="AccessKey ID")
    access_key_secret: Optional[str] = Field(None, description="AccessKey Secret（加密存储）")
    endpoint: Optional[str] = Field(None, description="默认 Endpoint")
    description: Optional[str] = Field(None, description="描述信息")

class CloudProviderUpdate(BaseModel):
    provider_name: Optional[str] = Field(None, description="云厂商名称")
    access_key_id: Optional[str] = Field(None, description="AccessKey ID")
    access_key_secret: Optional[str] = Field(None, description="AccessKey Secret（加密存储）")
    endpoint: Optional[str] = Field(None, description="默认 Endpoint")
    description: Optional[str] = Field(None, description="描述信息")

class CloudProviderOut(BaseModel):
    id: int
    provider_code: str
    provider_name: str
    access_key_id: str
    access_key_secret: str
    endpoint: str
    description: Optional[str]

    class Config:
        from_attributes = True

class CloudProviderPage(BaseModel):
    page: int
    pageSize: int
    total: int
    items: List[CloudProviderOut]
