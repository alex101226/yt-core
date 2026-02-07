from sqlalchemy.orm import Session

from app.models.sso.role import Role

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