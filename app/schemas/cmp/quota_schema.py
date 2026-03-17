from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuotaCategoryOutSchema(BaseModel):
    id: int
    resource_type: str
    quota_name: str
    quota_code: str
    quantity_type: str
    description: Optional[str] = None
    enabled: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuotaCategoryToggleSchema(BaseModel):
    category_id: int = Field(..., description="配额类别ID")
    enabled: bool = Field(..., description="是否启用")


class QuotaApplyCreateSchema(BaseModel):
    member_id: Optional[int] = Field(None, description="会员ID")
    cloud_provider_code: str = Field(..., description="云厂商编码")
    quota_code: str = Field(..., description="配额编码")
    apply_quota: float = Field(..., description="申请配额")
    apply_remark: Optional[str] = Field(None, description="申请备注")


class QuotaApplyApproveSchema(BaseModel):
    apply_id: int = Field(..., description="申请ID")
    approve_remark: Optional[str] = Field(None, description="审批备注")


class QuotaApplyRejectSchema(BaseModel):
    apply_id: int = Field(..., description="申请ID")
    approve_remark: Optional[str] = Field(None, description="审批备注")


class QuotaApplyOutSchema(BaseModel):
    id: int
    member_id: int
    member_name: str
    cloud_provider_code: str
    quantity_type: str
    quota_name: str
    quota_code: str
    allocated_quota: float
    apply_quota: float
    apply_remark: Optional[str] = None
    created_by_name: Optional[str] = None
    approve_status: str
    approved_by_name: Optional[str] = None
    approve_remark: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class QuotaApplyPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[QuotaApplyOutSchema]
