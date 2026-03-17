from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.sso.role import Role
from app.models.sso.user import User

class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def role_create(self, **data):
        role_db = Role(**data)
        self.db.add(role_db)
        self.db.commit()
        self.db.refresh(role_db)
        return role_db

    def role_list(self):
        roles = self.db.query(Role).all()
        return roles

    def role_page_list(self, page: int, page_size: int, role_name: str = None):
        query = self.db.query(Role).order_by(Role.id.desc())
        if role_name:
            query = query.filter(Role.role_name.like(f"%{role_name}%"))
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def role_get_by_id(self, role_id: int):
        return self.db.query(Role).filter(Role.id == role_id).first()

    def role_get_by_code(self, role_code: str):
        return self.db.query(Role).filter(Role.role_code == role_code).first()

    def role_user_count(self, role_code: str) -> int:
        return self.db.query(User).filter(User.role_code == role_code).count()

    def role_downgrade_users(self, role_code: str, fallback_role_code: str):
        self.db.query(User).filter(User.role_code == role_code).update(
            {"role_code": fallback_role_code}
        )

    def role_delete(self, role: Role):
        self.db.delete(role)

    def role_update(self, role: Role, data: dict):
        for key, value in data.items():
            if hasattr(role, key):
                setattr(role, key, value)
        self.db.flush()
        self.db.refresh(role)
        return role
