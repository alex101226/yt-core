from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

from app.repositories.cmp.invoice_email_repo import InvoiceEmailRepo

class InvoiceEmailService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InvoiceEmailRepo(db)

    # 分页列表
    def invoice_email_page_list(self, user_id: int, page: int, page_size: int):
        items, total = self.repo.invoice_email_page_list(user_id, page, page_size)
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    # 创建邮件
    def invoice_email_create(self, user: dict, data: dict) -> bool:
        user_id = user.get('user_id')
        username = user.get('username')
        is_default = 1 if self.repo.count_by(user_id) == 0 else 0
        payload = {
            **data,
            "created_by": user_id,
            "created_by_name": username,
            "is_default": is_default,
        }

        if self.repo.find_email_by(data['email']):
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message=Message.DATA_DUPLICATE)

        result = self.repo.email_create(payload)

        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True


    # 邮件修改
    def invoice_email_update(self, data: dict) -> bool:
        find = self.repo.find_id_by(data['email_id'])
        if not find:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)

        if self.repo.find_email_by(data['email']):
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message="此邮件已存在")

        result = self.repo.email_update(data)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True


    #邮件删除
    def invoice_email_delete(self, email_id: int):
        find_email = self.repo.find_id_by(email_id)
        if not find_email:
            raise BusinessException(code=ErrorCode.DATA_DUPLICATE, message=Message.DATA_DUPLICATE)

        if find_email.is_default:
            raise BusinessException(code=ErrorCode.FAILED, message="默认邮件不能删除，如要删除，请先修改默认邮件")

        result = self.repo.email_delete(email_id)
        if not result:
            raise BusinessException(code=ErrorCode.FAILED, message=Message.FAILED)
        return True

    # 设置默认邮件
    def invoice_email_default(self, user_id: int, email_id: int):
        # 清楚默认的
        self.repo.clear_default(user_id)

        result = self.repo.email_save_default(email_id)
        if not result:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        return True
