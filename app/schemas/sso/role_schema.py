from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class RoleAddSchema(BaseModel):
    role_code: str = Field(..., description="权限编号")
    role_name: str = Field(..., description="权限名称")
    description: str = Field(None, description="权限描述")


class RoleUpdateSchema(BaseModel):
    role_id: int = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")


class RoleOutSchema(BaseModel):
    id: int
    role_code: str
    role_name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RolePageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[RoleOutSchema]
