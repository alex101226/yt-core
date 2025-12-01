# app/schemas/cmp/vpc_schema.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# -------------------------
# 1️⃣ 基础字段模型
# -------------------------
class VpcBase(BaseModel):
    vpc_id: str
    # resource_group_id: int
    description: Optional[str] = None
    resource_group_id: Optional[int] = None
    cloud_provider_code: str
    # cloud_certificate_id: int
    region_id: str
    network_type: str


# -------------------------
# 2️⃣ 创建用模型
# -------------------------
class VpcCreate(VpcBase):
    pass


# -------------------------
# 3️⃣ 更新用模型
# -------------------------
class VpcUpdate(BaseModel):
    vpc_id: Optional[str]
    description: Optional[str]
    resource_group_id: Optional[int]
    region_id: Optional[str]
    network_type: Optional[str]
    cloud_provider_code: Optional[str]


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
class VpcPage(BaseModel):
    total: int
    page: int
    pageSize: int
    items: List[VpcOut]
