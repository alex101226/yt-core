from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VoucherTemplateCreateSchema(BaseModel):
    cloud_provider_code: str = Field(..., description="云厂商编码")
    amount: float = Field(..., description="面值金额")
    description: Optional[str] = Field(None, description="描述/备注")


class VoucherTemplateOutSchema(BaseModel):
    id: int
    template_no: str
    cloud_provider_code: str
    amount: float
    description: Optional[str] = None
    is_expired: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VoucherTemplatePageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[VoucherTemplateOutSchema]


class VoucherAssignCreateSchema(BaseModel):
    template_id: int = Field(..., description="模板ID")
    member_ids: List[int] = Field(..., description="会员ID列表")
    valid_start: datetime = Field(..., description="生效开始时间(UTC)")
    valid_end: datetime = Field(..., description="生效结束时间(UTC)")
    quantity: int = Field(..., description="份数")
    description: Optional[str] = Field(None, description="描述/备注")


class VoucherAssignOutSchema(BaseModel):
    assign_id: int
    member_id: int
    member_name: str
    cloud_provider_code: str
    amount: float
    consumed_amount: float = 0
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class VoucherAssignPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[VoucherAssignOutSchema]
