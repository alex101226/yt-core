from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.cmp.invoice_repo import InvoiceRepo

class InvoiceService:
    def __init__(self, db: Session):
        self.db = db
        self.invoice_repo = InvoiceRepo(db)

    # 设置发票抬头
    def setting_invoice(self, user_id: int, data: dict):
        payload = {
            **data,
            "user_id": user_id,
            "is_default": True,
            "status": 'enabled',
        }
        result = self.invoice_repo.setting_invoice(payload)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True

    # 获取发票抬头
    def invoice_info(self, user_id: int):
        result = self.invoice_repo.find_by_user_id(user_id) or {}
        if not result:
            return {
                "invoice_title": '',
                "title_type": '',
                "invoice_type": '',
                "bank_name": '',
                "bank_account": '',
                "company_address": '',
                "company_phone": '',
                "taxpayer_id": '',
            }
        return {
            "invoice_title": result.invoice_title,
            "title_type": result.title_type,
            "invoice_type": result.invoice_type,
            "bank_name": result.bank_name,
            "bank_account": result.bank_account,
            "company_address": result.company_address,
            "company_phone": result.company_phone,
            "taxpayer_id": result.taxpayer_id,
        }