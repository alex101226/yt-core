from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.sso.session import UserSession
from app.core.security import create_access_token, create_refresh_token
from app.core.config import settings
from app.repositories.sso.session_repo import SessionRepository


class SessionService:
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = SessionRepository(db)

    def create_session_for_user(self, user):
        refresh_token = create_refresh_token({"sub": str(user.id)})
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # 存入 DB（refresh session）
        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,  # 可以 hash 后存储更安全
            expires_at=expires_at,
        )
        # 存入数据库
        self.session_repo.create(session)

        # access token
        access_token = create_access_token({"sub": str(user.id)})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user
        }
