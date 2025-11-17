from typing import List, Tuple
from sqlalchemy.orm import Session
from app.repositories.public.resource_group_repo import ResourceGroupRepository
from app.models.public.resource_group import ResourceGroup
from app.common.exceptions import BusinessException
from app.common.messages import Message
from app.common.status_code import ErrorCode

class ResourceGroupService:
    """资源组业务服务层"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ResourceGroupRepository(db)

    def create_group(self, data: dict) -> ResourceGroup:
        # 检查 code 是否已存在
        exists = self.repo.get_by_code(data["code"])
        if exists:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_EXISTS,
                message=Message.RESOURCE_GROUP_EXISTS
            )
        return self.repo.create(data)

    def get_group(self, record_id: int) -> ResourceGroup:
        obj = self.repo.get_by_id(record_id)
        if not obj:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )
        return obj

    def list_groups(self, page: int, page_size: int) -> Tuple[int, List[ResourceGroup]]:
        return self.repo.list_page(page, page_size)

    def update_group(self, record_id: int, data: dict) -> ResourceGroup:
        obj = self.repo.update(record_id, data)
        if not obj:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )
        return obj

    def delete_group(self, record_id: int) -> None:
        success = self.repo.delete(record_id)
        if not success:
            raise BusinessException(
                code=ErrorCode.RESOURCE_GROUP_NOT_FOUND,
                message=Message.RESOURCE_GROUP_NOT_FOUND
            )
