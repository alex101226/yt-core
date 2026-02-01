from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger

from app.models.cmp.invoice_email import InvoiceEmail

class InvoiceEmailRepo:
    def __init__(self, db: Session):
        self.db = db

    # 返回分页列表
    def invoice_email_page_list(self, user_id: int, page: int, page_size: int):
        query = self.db.query(InvoiceEmail).filter(
            InvoiceEmail.created_by == user_id,
            InvoiceEmail.is_released==0
        ).order_by(InvoiceEmail.id.desc())

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    #   创建邮件
    def email_create(self, data: dict):
        email = InvoiceEmail(**data)
        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)
        return email

    # 邮件修改
    def email_update(self, data: dict):
        find = self.find_id_by(data['email_id'])
        find.email = data['email']
        self.db.commit()
        self.db.refresh(find)
        return find

    # 删除
    def email_delete(self, email_id: int):
        result = self.find_id_by(email_id)
        if not result:
            return None
        result.is_released = True
        self.db.commit()
        self.db.refresh(result)
        return result

    # 切换默认
    def email_save_default(self, email_id: int):
        find = self.find_id_by(email_id)
        if not find:
            return None
        find.is_default = True
        self.db.commit()
        self.db.refresh(find)
        return find

    # 清除默认
    def clear_default(self, user_id: int):
        self.db.query(InvoiceEmail).filter(
            InvoiceEmail.user_id == user_id,
            InvoiceEmail.is_default == 1
        ).update({InvoiceEmail.is_default: 0})
        self.db.commit()


    # 查找表里是否有内容
    def count_by(self, user_id: int) -> Optional[int]:
        return self.db.query(InvoiceEmail).filter(InvoiceEmail.user_id == user_id).count()

    # 查找表里是否存在同一个邮件
    def find_email_by(self, email: str) -> Optional[InvoiceEmail]:
        return self.db.query(InvoiceEmail).filter(InvoiceEmail.email == email).first()

    # 根据id查找
    def find_id_by(self, email_id: int) -> Optional[int]:
        return self.db.query(InvoiceEmail).filter(InvoiceEmail.id == email_id, InvoiceEmail.is_released == 0).first()

