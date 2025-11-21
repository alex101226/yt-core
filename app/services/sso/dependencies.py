from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db
from .auth_service import AuthService

def get_user_service(db: Session = Depends(get_sso_db)) -> AuthService:
    return AuthService(db)