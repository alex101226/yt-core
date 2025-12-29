from pydantic import BaseModel, EmailStr


class InvoiceEmailSchema(BaseModel):
    email: EmailStr

class InvoiceEmailUpdate(InvoiceEmailSchema):
    email_id: int