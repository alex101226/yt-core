from datetime import datetime
from pydantic import BaseModel
from pydantic.v1 import Field


class CloudRegionBase(BaseModel):
    provider_code: str = Field(..., description="云厂商编码，例如 aliyun")
    region_id: str = Field(..., description="地区代号，例如 cn-hangzhou")
    region_name: str = Field(..., description="地区名称，例如 华东1（杭州）")


class CloudRegionOut(CloudRegionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
