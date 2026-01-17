from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


class InvoiceSchema(BaseModel):
    invoice_title: str
    title_type: str
    invoice_type: str
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    taxpayer_id: Optional[str] = None


class InvoiceItemSchema(BaseModel):
    user_id: int = Field(..., description="用户ID", json_schema_extra={"example": 123})
    billing_period: str = Field(..., description="账期", json_schema_extra={"example": "2026-01"})
    billing_period_start: datetime = Field(..., description="账期开始时间",
                                           json_schema_extra={"example": "2026-01-01T00:00:00Z"})
    billing_period_end: Optional[datetime] = Field(None, description="账期结束时间",
                                         json_schema_extra={"example": "2026-01-31T23:59:59Z"})
    cloud_provider_code: str = Field(..., description="云厂商代码", json_schema_extra={"example": "aliyun"})
    cloud_provider_name: str = Field(..., description="云厂商名称", json_schema_extra={"example": "阿里云"})
    order_type: str = Field(..., description="下单类型 new/renew/upgrade", json_schema_extra={"example": "renew"})
    product_display_name: str = Field(..., description="产品展示名称",
                                      json_schema_extra={"example": "包年 · 2026-01 · 云服务器 ECS"})
    origin_order_no: str = Field(..., description="原始订单号", json_schema_extra={"example": "ORD123456789"})
    instance_id: Optional[str] = Field(None, description="实例ID，可为空", json_schema_extra={"example": "i-abcdef123"})
    paid_amount: float = Field(..., description="订单实付金额", json_schema_extra={"example": 120.00})
    invoice_amount: float = Field(..., description="可开票金额", json_schema_extra={"example": 120.00})
    paid_at: datetime = Field(..., description="订单支付时间", json_schema_extra={"example": "2026-01-15T10:23:00Z"})

# ===============================
# 新增可开票记录 Schema
# （扣费完成后生成使用）
# ===============================
class InvoiceItemCreateSchema(InvoiceItemSchema):
    pass


# 开票记录
class InvoiceRecordSchema(BaseModel):
    email: EmailStr = Field(..., description="邮箱"),
    invoice_item_ids: List[str] = Field(..., description="发票ids")
    invoice_type: str = Field(..., description="发票类型，'GENERAL=增值税普通发票','SPECIAL=增值税专用发票'")
    invoice_item_id: int = Field(..., description="发票抬头id")
    amount: float = Field(..., description="发票的金额")



