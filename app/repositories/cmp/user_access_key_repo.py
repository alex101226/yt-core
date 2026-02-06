from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.cmp import UserAccessKey

class UserAccessKeyRepo:
    def __init__(self, session: Session):
        self._session = session

    # 创建密钥
    def create_access_key(self, data: dict):
        keys = UserAccessKey(**data)
        self._session.add(keys)
        self._session.commit()
        self._session.refresh(keys)
        return keys

    # ak列表
    def get_access_key_page_list(self, parent_id: int, page: int, page_size: int):
        filters = [UserAccessKey.created_by == parent_id, UserAccessKey.is_released == 0]
        q = (self._session.query(UserAccessKey)
             .filter(*filters)
             .order_by(UserAccessKey.id.desc()))
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # 单条查询
    def get_by_id(self, access_key_id: int) -> Optional[UserAccessKey]:
        return self._session.query(UserAccessKey).filter(UserAccessKey.id == access_key_id).first()

    # 禁用
    def set_disabled(self, access_key_id: int):
        find = self.get_by_id(access_key_id)
        if not find:
            return False
        find.status = False
        self._session.commit()
        self._session.refresh(find)
        return find

    # 删除
    def set_release(self, access_key_id: int):
        find = self.get_by_id(access_key_id)
        if not find:
            return False
        find.is_released = True
        self._session.commit()
        self._session.refresh(find)
        return find