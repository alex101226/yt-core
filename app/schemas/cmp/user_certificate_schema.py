from pydantic import BaseModel, Field
from typing import Optional, List

class CertificateBase(BaseModel):
    cloud_code: str = Field(..., description="云凭证编码，例如 aliyun")
    cloud_name: str = Field(..., description="云凭证名称")
    description: Optional[str] = Field(None, description="描述信息")

class UserCertificateOut(CertificateBase):
    id: int
    created_by: int
    created_by_name: str

    class Config:
        from_attributes = True

class UserCertificateCreate(CertificateBase):
    cloud_access_key_id: str = Field(..., description="AccessKey ID")
    cloud_access_key_secret: str = Field(..., description="AccessKey Secret（加密存储）")
    pass

class UserCertificateUpdate(BaseModel):
    cloud_name: Optional[str] = Field(None, description="云凭证名称")
    cloud_access_key_id: Optional[str] = Field(None, description="AccessKey ID")
    cloud_access_key_secret: Optional[str] = Field(None, description="AccessKey Secret（加密存储）")
    description: Optional[str] = Field(None, description="描述信息")

class UserCertificatePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[UserCertificateOut]


class UserCertificateList(CertificateBase):
    id: int
    is_default: int

    class Config:
        from_attributes = True
