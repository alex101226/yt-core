# app/schemas/cmp/vpc_schema.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# -------------------------
# 1️⃣ 基础字段模型
# -------------------------
class VpcBase(BaseModel):
    name: str = Field(..., description="VPC 名称")
    description: Optional[str] = Field(None, description="VPC 描述信息")
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    cloud_provider_id: int = Field(..., description="云厂商ID")
    cloud_certificate_id: int = Field(..., description="云凭证ID")
    region_id: str = Field(..., description="区域ID")
    network_type: str = Field(..., description="网络类型，例如 VPC/CLASSIC")


# -------------------------
# 2️⃣ 创建用模型
# -------------------------
class VpcCreate(VpcBase):
    pass


# -------------------------
# 3️⃣ 更新用模型
# -------------------------
class VpcUpdate(BaseModel):
    name: Optional[str] = Field(None, description="VPC 名称")
    description: Optional[str] = Field(None, description="VPC 描述信息")
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    region_id: Optional[str] = Field(None, description="区域ID")
    network_type: Optional[str] = Field(None, description="网络类型")


# -------------------------
# 4️⃣ 输出用模型
# -------------------------
class VpcOut(VpcBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# -------------------------
# 5️⃣ 分页用模型
# -------------------------
from typing import List

class VpcPage(BaseModel):
    total: int
    page: int
    pageSize: int
    items: List[VpcOut]
