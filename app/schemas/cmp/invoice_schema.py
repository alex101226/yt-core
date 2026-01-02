from typing import Optional

from pydantic import BaseModel, EmailStr


class InvoiceSchema(BaseModel):
    invoice_title: str
    title_type: str
    invoice_type: str
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    taxpayer_id: Optional[str] = None