from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional, Any

from app.models.cmp.dict_item import DictItem
from app.schemas.cmp.dict_schema import DictItemCreate, DictItemUpdate, DictItemListOut, DictItemOut


class DictRepository:
    def __init__(self, db: Session):
        self.db = db

    # -----------------------------
    # 创建字典项
    # -----------------------------
    def create(self, obj_in: DictItemCreate) -> DictItem:
        db_obj = DictItem(
            type_code=obj_in.type_code,
            item_code=obj_in.item_code,
            item_name=obj_in.item_name,
            description=obj_in.description
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    # -----------------------------
    # 根据 type_code + item_code 查单条字典项
    # -----------------------------
    def get_by_code(self, type_code: str, item_code: str) -> Optional[DictItem]:
        return (
            self.db.query(DictItem)
            .filter(DictItem.type_code == type_code, DictItem.item_code == item_code)
            .first()
        )

    #   根据id获取
    def get_by_id(self, dict_id: int) -> Optional[DictItem]:
        return self.db.get(DictItem, dict_id)

    # -----------------------------
    # 根据 type_code 查询所有字典项
    # -----------------------------
    def list_by_type(self, type_code: str) -> list[type[DictItem]]:
        return (
            self.db.query(DictItem)
            .filter_by(type_code = type_code)
            .order_by(DictItem.id.asc())
            .all()
        )

    # -----------------------------
    # 更新字典项
    # -----------------------------
    def update(self, db_obj: DictItem, obj_in: DictItemUpdate) -> DictItem:
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    # -----------------------------
    # 删除字典项
    # -----------------------------
    def delete(self, db_obj: DictItem) -> None:
        self.db.delete(db_obj)
        self.db.commit()

    # -----------------------------
    # 分页查询（可按 type_code + keyword 模糊查询）
    # -----------------------------
    def list(
        self,
        type_code: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> DictItemListOut:
        query = self.db.query(DictItem)
        if type_code:
            query = query.filter_by(type_code = type_code)
        if keyword:
            like_keyword = f"%{keyword}%"
            query = query.filter(
                (DictItem.item_name.ilike(like_keyword)) | (DictItem.item_code.ilike(like_keyword))
            )
        total = query.count()
        db_items = query.order_by(DictItem.id.asc()).offset((page - 1) * size).limit(size).all()
        items = [DictItemOut.model_validate(obj) for obj in db_items]
        return DictItemListOut(total=total, items=items)
