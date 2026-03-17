from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreditGrantCreateSchema(BaseModel):
    member_id: int = Field(..., description="会员ID")
    amount: float = Field(..., description="充值金额")
    cloud_provider_code: str = Field(..., description="云厂商编码")
    valid_start: datetime = Field(..., description="生效开始时间(UTC)")
    valid_end: datetime = Field(..., description="生效结束时间(UTC)")
    description: Optional[str] = Field(None, description="描述/备注")


class CreditGrantOutSchema(BaseModel):
    id: int
    member_id: int
    member_name: str
    member_account: Optional[str] = None
    amount: float
    remaining_amount: float
    cloud_provider_code: str
    valid_start: datetime
    valid_end: datetime
    status: str
    source_type: str
    approve_status: str
    audit_result: Optional[str] = None
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    reject_reason: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreditGrantPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[CreditGrantOutSchema]


class CreditBalanceItemSchema(BaseModel):
    cloud_provider_code: str
    total_amount: float
    distributed_amount: float
    expired_amount: float
    remaining_amount: float


class CreditBalanceSchema(BaseModel):
    member_id: int
    member_name: str
    total_amount: float
    distributed_amount: float
    expired_amount: float
    remaining_amount: float
    items: List[CreditBalanceItemSchema]


class CreditFlowOutSchema(BaseModel):
    id: int
    grant_id: Optional[int] = None
    member_id: int
    member_name: str
    member_account: Optional[str] = None
    amount: float
    direction: str
    flow_type: str
    cloud_provider_code: Optional[str] = None
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class CreditFlowPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[CreditFlowOutSchema]


class CreditApproveSchema(BaseModel):
    grant_id: int = Field(..., description="充值记录ID")


class CreditRejectSchema(BaseModel):
    grant_id: int = Field(..., description="充值记录ID")
    reason: Optional[str] = Field(None, description="驳回原因")


class CreditTrendPointSchema(BaseModel):
    date: str
    value: float


class CreditTopMemberSchema(BaseModel):
    member_id: int
    member_name: str
    value: float


class CreditOverviewSummarySchema(BaseModel):
    remaining_distributable_amount: float
    total_amount: float
    expired_amount: float
    distributed_amount: float
    today_distributed_amount: float


class CreditOverviewCardsSchema(BaseModel):
    today_new_order_count: int
    today_consume_amount: float
    today_distributed_member_count: int
    today_consume_member_count: int
    total_order_count: int
    total_consume_amount: float
    total_distributed_member_count: int
    total_consume_member_count: int


class CreditOverviewSchema(BaseModel):
    summary: CreditOverviewSummarySchema
    cards: CreditOverviewCardsSchema
    recent_order_trend: List[CreditTrendPointSchema]
    recent_consume_amount_trend: List[CreditTrendPointSchema]
    today_order_top10_members: List[CreditTopMemberSchema]
    today_amount_top10_members: List[CreditTopMemberSchema]
