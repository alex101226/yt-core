# app/schemas/cmp/vpc_schema.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


# -------------------------
# 1️⃣ 基础字段模型
# -------------------------
class VpcBase(BaseModel):
    vpc_name: str
    description: Optional[str] = None
    resource_group_id: Optional[int] = None
    cloud_provider_code: str
    region_id: str
    network_type: str
    service_cidr: str


# -------------------------
# 4️⃣ 输出用模型
# -------------------------
class VpcOut(VpcBase):
    id: int
    vpc_id: str
    status: str
    service_cidr: Optional[str]
    created_at: datetime
    updated_at: datetime
    used_count: Optional[int] = 0

    class Config:
        from_attributes = True

# 返回列表
class VpcList(VpcOut):
    resource_group_name: Optional[str]
    sync_status: Optional[int]
    subnet_count: Optional[int] = 0

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
# 5️⃣ 分页用模型
# -------------------------
class VpcPage(BaseModel):
    total: int
    page: int
    pageSize: int
    items: List[VpcList]
