from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# -------------------------
# 公用基础字段
# -------------------------
class DictItemBase(BaseModel):
    type_code: str = Field(..., description="字典类型标识，例如 NETWORK_TYPE")
    item_code: str = Field(..., description="字典项编码，例如 VPC / CLASSIC")
    item_name: str = Field(..., description="字典项名称，例如 专有网络 / 经典网络")
    description: Optional[str] = Field(None, description="描述信息")


# -------------------------
# 创建字典项
# -------------------------
class DictItemCreate(DictItemBase):
    """创建字典项"""
    pass


# -------------------------
# 更新字典项（部分字段可选）
# -------------------------
class DictItemUpdate(BaseModel):
    # type_code: Optional[str] = Field(None, description="字典类型标识")
    item_code: Optional[str] = Field(None, description="字典项编码")
    item_name: Optional[str] = Field(None, description="字典项名称")
    description: Optional[str] = Field(None, description="描述")


# -------------------------
# 返回给前端的字典项数据
# -------------------------
class DictItemOut(BaseModel):
    type_code: str = Field(..., description="字典类型标识，例如 NETWORK_TYPE")
    item_code: str = Field(..., description="字典项编码，例如 VPC / CLASSIC")
    item_name: str = Field(..., description="字典项名称，例如 专有网络 / 经典网络")
    description: Optional[str] = Field(None, description="描述信息")
    created_at: datetime = Field(..., description="创建时间（UTC）")
    updated_at: datetime = Field(..., description="更新时间（UTC）")

    class Config:
        from_attributes = True  # FastAPI ORM Mode



# -------------------------
# 列表查询
# -------------------------
class DictItemQuery(BaseModel):
    type_code: Optional[str] = Field(None, description="按字典类型筛选")
    keyword: Optional[str] = Field(None, description="按名称或编码模糊查询")
    page: int = Field(1, description="页码，从1开始")
    size: int = Field(10, description="每页条数")


# -------------------------
# 列表返回（分页）
# -------------------------
class DictItemListOut(BaseModel):
    total: int = Field(..., description="总条数")
    items: list[DictItemOut] = Field(..., description="数据列表")
