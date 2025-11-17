from sqlalchemy.orm import Session
from app.repositories.public.resource_group_binding_repo import ResourceGroupBindingRepository
from app.schemas.public.resource_group_binding_schema import (
    ResourceGroupBindingCreate,
)
from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode
from app.common.messages import Message

class ResourceGroupBindingService:
    def __init__(self, db: Session):
        self.db = db
        self.binding_repo = ResourceGroupBindingRepository(db)

    # 创建绑定
    def bind(self, data: ResourceGroupBindingCreate):
        # 检查资源是否已经绑定
        exists = self.binding_repo.get_by_resource(
            data.resource_type,
            data.resource_id,
        )
        if exists:
            raise BusinessException(
                code=ErrorCode.RESOURCE_ALREADY_BOUND,
                message=Message.RESOURCE_ALREADY_BOUND
            )

        return self.binding_repo.create(data.model_dump())

    # 删除绑定
    def unbind(self, binding_id: int):
        binding = self.binding_repo.get(binding_id)
        if not binding:
            raise BusinessException(
                code=ErrorCode.RESOURCE_BINDING_NOT_FOUND,
                message=Message.RESOURCE_BINDING_NOT_FOUND
            )

        self.binding_repo.delete(binding)
        return True

    # 获取资源组绑定列表
    def list_bindings(self, group_id: int, page: int, page_size: int):
        return self.binding_repo.list_by_group_page(group_id, page, page_size)
