from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.cmp.user_certificate import UserCertificate

class UserCertificateRepository:
    def __init__(self, db: Session):
        self.db = db

    # 创建云凭证
    def create(self, data: dict) -> UserCertificate:
        obj = UserCertificate(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    # 根据id查询云凭证一条记录
    def get_by_id(self, record_id: int) -> Optional[UserCertificate]:
        return self.db.get(UserCertificate, record_id)

    # 根据code查询云凭证一条记录
    def get_by_code(self, cloud_code: str) -> Optional[UserCertificate]:
        return self.db.query(UserCertificate).filter_by(cloud_code=cloud_code).first()

    # 下拉选择list
    def certificate_list(self, user_id: int):
        items = self.db.query(
            UserCertificate.id,
            UserCertificate.cloud_code,
            UserCertificate.cloud_name,
            UserCertificate.is_default,
            UserCertificate.description
        ).filter_by(created_by=user_id).all()
        return items

    # 返回云凭证列表
    def list_page(self, user_id, page: int, page_size: int):
        q = self.db.query(
            UserCertificate.id,
            UserCertificate.cloud_code,
            UserCertificate.cloud_name,
            UserCertificate.is_default,
            UserCertificate.description,
            UserCertificate.created_by,
            UserCertificate.created_by_name,
        ).filter(UserCertificate.created_by == user_id).order_by(UserCertificate.id.desc())
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return total, items

    # 更新云凭证信息
    def update(self, record_id: int, **kwargs) -> Optional[UserCertificate]:
        obj = self.get_by_id(record_id)
        if not obj:
            return None
        for k, v in kwargs.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    #  删除云凭证
    def delete(self, record_id: int) -> bool:
        obj = self.get_by_id(record_id)
        if not obj or obj.is_default == 1:
            return False
        self.db.delete(obj)
        self.db.commit()
        return obj

    # 查询用户是否已有凭证
    def count_by_user(self, user_id: int):
        return self.db.query(UserCertificate).filter(
            UserCertificate.created_by == user_id
        ).count()

    # 清除用户所有的默认凭证
    def clear_default(self, user_id: int):
        self.db.query(UserCertificate).filter(
            UserCertificate.created_by == user_id,
            UserCertificate.is_default == 1
        ).update({UserCertificate.is_default: 0})
        self.db.commit()

    # 设置默认云凭证
    def set_default(self, record_id: int):
        obj = self.db.query(UserCertificate).filter(
            UserCertificate.id == record_id
        ).first()
        if obj:
            obj.is_default = 1
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def get_certificate_find(self, user_id: int):
        return self.db.query(
            UserCertificate.id,
            UserCertificate.cloud_code,
            UserCertificate.cloud_name
        ).filter(
            UserCertificate.created_by == user_id,
            UserCertificate.is_default == 1
        ).first()

    # 获取用户的ak
    def get_user_ak(self, user_id: int):
       find = self.db.query(
           UserCertificate.cloud_code,
           UserCertificate.cloud_access_key_id,
           UserCertificate.cloud_access_key_secret
       ).filter(
           UserCertificate.created_by == user_id,
           UserCertificate.is_default == 1
       ).first()
       return find