from typing import Optional
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.models.cmp.resource_group import ResourceGroup, ResourceGroupBinding
from app.schemas.cmp.resource_group_schema import ResourceGroupBindingCreate

"""资源组仓储层"""
class ResourceGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建资源组
    def create_group(self, data: dict) -> ResourceGroup:

        obj = ResourceGroup(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # 根据id查找资源组
    def get_by_group_id(self, group_id: int) -> Optional[ResourceGroup]:
        return self.db.query(ResourceGroup).filter_by(id=group_id).first()

    # 根据code查找资源组
    def get_by_group_code(self, code: str) -> Optional[ResourceGroup]:
        return self.db.query(ResourceGroup).filter_by(rg_code = code).first()

    # 资源组列表，带分页
    def group_list_page(self, user_id: int, page: int, page_size: int) -> tuple[int, list[type[ResourceGroup]]]:
        query = self.db.query(ResourceGroup).filter(
            ResourceGroup.created_by == user_id
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # 更新资源组
    def group_update(self, record_id: int, data: dict) -> Optional[ResourceGroup]:
        obj = self.get_by_group_id(record_id)
        if not obj:
            return None
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # 删除资源组
    def group_delete(self, record_id: int) -> bool:
        obj = self.get_by_group_id(record_id)
        if not obj:
            return False
        self.db.delete(obj)
        self.db.commit()
        return True


    # 绑定资源
    def resource_bind_create(self, data: dict) -> ResourceGroupBinding:
        obj = ResourceGroupBinding(**data)
        self.db.add(obj)
        self.db.flush()
        # self.db.commit()
        # self.db.refresh(obj)
        return obj

    # 删除绑定资源
    def resource_bind_delete(self, binding: ResourceGroupBinding):
        self.db.delete(binding)
        self.db.commit()

    # 按ID获取绑定的资源
    def get_resource_bind_id(self, binding_id: int) -> Optional[ResourceGroupBinding]:
        return self.db.get(ResourceGroupBinding, binding_id)

    # 查询资源是否已绑定
    def get_by_resource_bind(self, resource_type: str, resource_id: str) -> Optional[ResourceGroupBinding]:
        find = self.db.query(ResourceGroupBinding).filter_by(resource_type=resource_type, resource_id=resource_id).first()
        return find

    # 获取某组下的绑定（分页）
    def resource_bind_list_page(self, group_id: int, page: int, page_size: int):
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
