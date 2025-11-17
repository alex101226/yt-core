from pydantic import BaseModel, Field
from typing import Optional, List

class CloudCertificateBase(BaseModel):
    cloud_code: str = Field(..., description="云凭证编码，例如 aliyun")
    cloud_name: str = Field(..., description="云凭证名称")
    cloud_access_key_id: str = Field(..., description="AccessKey ID")
    cloud_access_key_secret: str = Field(..., description="AccessKey Secret（加密存储）")
    description: Optional[str] = Field(None, description="描述信息")

class CloudCertificateOut(BaseModel):
    id: int
    cloud_code: str
    cloud_name: str
    cloud_access_key_id: str
    cloud_access_key_secret: str
    description: Optional[str]

    class Config:
        from_attributes = True

class CloudCertificateCreate(BaseModel):
    cloud_code: Optional[str] = Field(None, description="云凭证唯一code")
    cloud_name: Optional[str] = Field(None, description="云凭证名称")
    cloud_access_key_id: Optional[str] = Field(None, description="AccessKey ID")
    cloud_access_key_secret: Optional[str] = Field(None, description="AccessKey Secret（加密存储）")
    description: Optional[str] = Field(None, description="描述信息")

class CloudCertificateUpdate(BaseModel):
    cloud_name: Optional[str] = Field(None, description="云凭证名称")
    cloud_access_key_id: Optional[str] = Field(None, description="AccessKey ID")
    cloud_access_key_secret: Optional[str] = Field(None, description="AccessKey Secret（加密存储）")
    description: Optional[str] = Field(None, description="描述信息")

class CloudCertificatePage(BaseModel):
    page: int
    pageSize: int
    total: int
    items: List[CloudCertificateOut]
