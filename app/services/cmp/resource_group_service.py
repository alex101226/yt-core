from sqlalchemy.orm import Session
from app.repositories.cmp.resource_group_repo import ResourceGroupRepository
from app.schemas.cmp.resource_group_schema import ResourceGroupCreate, ResourceGroupBindingCreate

from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode

from app.core.logger import logger

"""资源组业务服务层"""
class ResourceGroupService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ResourceGroupRepository(db)

    # 创建资源组
    def create_group(self, data: dict):
        # 检查 code 是否已存在
        exists = self.repo.get_by_group_code(data['rg_code'])
        if exists:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_EXISTS,
                message=Message.RESOURCE_GROUP_EXISTS
            )
        result = self.repo.create_group(data)
        # logger.info(f'创建返回的数据查看 {result}')
        return result

    # 根据id查找资源组
    def get_group(self, group_id: int):
        obj = self.repo.get_by_group_id(group_id)
        if not obj:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )
        return obj

    # 资源组列表，带分页
    def list_groups(self, user_id: int, page: int, page_size: int):
        return self.repo.group_list_page(user_id, page, page_size)

    # 更新资源组
    def update_group(self, record_id: int, data: dict):
        obj = self.repo.group_update(record_id, data)
        if not obj:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )
        return obj

    # 删除资源组
    def delete_group(self, record_id: int) -> None:
        success = self.repo.group_delete(record_id)
        if not success:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )


    # 创建绑定
    def bind(self, data: ResourceGroupBindingCreate):
        # 检查资源是否已经绑定
        exists = self.repo.get_by_resource_bind(
            data.resource_type,
            data.resource_id,
        )
        if exists:
            raise BusinessException(
                code=ErrorCode.RESOURCE_ALREADY_BOUND,
                message=Message.RESOURCE_ALREADY_BOUND
            )

        resource_find = self.repo.get_by_group_id(data.resource_group_id)
        if not resource_find:
            raise BusinessException(
                code=ErrorCode.RESOURCE_BINDING_NOT_FOUND,
                message=Message.RESOURCE_BINDING_NOT_FOUND
            )
        payload = {
            **data.model_dump(),
            "resource_name": resource_find.rg_name
        }
        return self.repo.resource_bind_create(payload)

    # 删除绑定
    def unbind(self, binding_id: int):
        binding = self.repo.get_resource_bind_id(binding_id)
        if not binding:
            raise BusinessException(
                code=ErrorCode.RESOURCE_BINDING_NOT_FOUND,
                message=Message.RESOURCE_BINDING_NOT_FOUND
            )

        self.repo.resource_bind_delete(binding)
        return True

    # 获取资源组绑定列表
    def list_bindings(self, group_id: int, page: int, page_size: int):
        return self.repo.resource_bind_list_page(group_id, page, page_size)
