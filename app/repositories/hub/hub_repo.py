from typing import Optional

from sqlalchemy.orm import Session

from app.models.hub.categoire import HubCategories
from app.models.hub.models import HubModels

class HubRepo:
    def __init__(self, session: Session):
        self.session = session

    # 返回分类列表
    def categories_list(self):
        return self.session.query(HubCategories).all()

    # 返回模型数据列表
    def model_list(self):
        return self.session.query(HubModels).all()

    # 返回详情
    def model_detail(self, slug: str):
        return self.session.query(HubModels).filter_by(slug=slug).first()

