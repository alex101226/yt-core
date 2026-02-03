from sqlalchemy.orm import Session

from app.models.cmp.invoice import Invoice

class InvoiceRepo:
    def __init__(self, db: Session):
        self.db = db

    # 设置
    def setting_invoice(self, data: dict):

        find = self.find_by_user_id(data['created_by'])
        if not find:
            return self.create(data)
        return self.update(find, data)

    # 创建
    def create(self, data: dict):
        invoice = Invoice(**data)
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # 修改
    def update(self, invoice, data: dict):
        for key, value in data.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)

        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    # 查询
    def find_by_user_id(self, user_id: int):
        record = self.db.query(Invoice).filter_by(created_by=user_id).first()
        return record