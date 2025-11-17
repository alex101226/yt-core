from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.public.resource_group import ResourceGroupBinding


class ResourceGroupBindingRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建绑定
    def create(self, data: dict) -> ResourceGroupBinding:
        obj = ResourceGroupBinding(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # 删除绑定
    def delete(self, binding: ResourceGroupBinding):
        self.db.delete(binding)
        self.db.commit()

    # 按ID获取
    def get(self, binding_id: int) -> Optional[ResourceGroupBinding]:
        return self.db.get(ResourceGroupBinding, binding_id)

    # 查询资源是否已绑定
    def get_by_resource(self, resource_type: str, resource_id: str) -> Optional[ResourceGroupBinding]:
        return (
            self.db.query(ResourceGroupBinding)
            .filter_by(resource_type=resource_type, resource_id=resource_id)
            .first()
        )

    # 获取某组下的绑定（分页）
    def list_by_group_page(self, group_id: int, page: int, page_size: int):
        query = self.db.query(ResourceGroupBinding).filter_by(resource_group_id=group_id)

        total = query.count()

        items = (
            query
            .order_by(ResourceGroupBinding.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return total, items

