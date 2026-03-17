from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MemberCreateSchema(BaseModel):
    member_name: str = Field(..., description="会员名称/企业名称")
    member_type: str = Field(..., description="会员类型：PERSONAL/COMPANY")
    credit_code: Optional[str] = Field(None, description="社会信用码")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    contact_email: Optional[str] = Field(None, description="邮箱")
    industry: Optional[str] = Field(None, description="行业分类")
    address: Optional[str] = Field(None, description="地址")
    description: Optional[str] = Field(None, description="描述/备注")

    member_person_name: Optional[str] = Field(None, description="会员姓名")
    member_account: str = Field(..., description="会员账号(用户账号)")


class MemberOutSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    member_name: str
    member_type: str
    credit_code: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    member_person_name: Optional[str] = None
    member_account: Optional[str] = None
    is_frozen: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MemberPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[MemberOutSchema]
