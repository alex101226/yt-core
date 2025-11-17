from typing import List, Optional
from sqlalchemy.orm import Session

from app.common.exceptions import BusinessException
from app.repositories.cmp.dict_repo import DictRepository
from app.schemas.cmp.dict_schema import (
    DictItemCreate,
    DictItemUpdate,
    DictItemOut,
    DictItemListOut
)

class DictService:
    """字典业务逻辑层，只调用 Repository"""

    def __init__(self, db: Session):
        self.repo = DictRepository(db)

    # -------------------------
    # 创建字典项
    # -------------------------
    def create(self, obj_in: DictItemCreate) -> DictItemOut:
        db_obj = self.repo.create(obj_in)
        return DictItemOut.model_validate(db_obj)

    # -------------------------
    # 更新字典项
    # -------------------------
    def update(self, type_code: str, item_code: str, obj_in: DictItemUpdate) -> Optional[DictItemOut]:
        db_obj = self.repo.get_by_code(type_code, item_code)
        if not db_obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        updated_obj = self.repo.update(db_obj, obj_in)
        return DictItemOut.model_validate(updated_obj)

    # -------------------------
    # 删除字典项
    # -------------------------
    def delete(self, dict_id: int) -> bool:
        db_obj = self.repo.get_by_id(dict_id)
        if not db_obj:
            raise BusinessException(code=ErrorCode.DATA_NOT_FOUND, message=Message.DATA_NOT_FOUND)
        self.repo.delete(db_obj)
        return True

    # -------------------------
    # 查询某类型下的字典项
    # -------------------------
    def list_by_type(self, type_code: str) -> List[DictItemOut]:
        db_items = self.repo.list_by_type(type_code)
        return [DictItemOut.model_validate(obj) for obj in db_items]

    # -------------------------
    # 分页查询
    # -------------------------
    def list(
        self,
        type_code: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> DictItemListOut:
        return self.repo.list(type_code=type_code, keyword=keyword, page=page, size=size)
