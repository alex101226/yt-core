# app/repositories/session_repository.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.sso.session import UserSession

class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, session: UserSession) -> UserSession:
        # s = UserSession(user_id=user_id, refresh_token=refresh_token, expires_at=expires_at, ip=ip, user_agent=user_agent)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_user_id(self, user_id: int):
        return self.db.query(UserSession).filter(UserSession.user_id == user_id).all()

    def clear_user_sessions(self, user_id: int):
        """删除该用户所有会话（实现单点登录）"""
        self.db.query(UserSession).filter(UserSession.user_id == user_id).delete()
        self.db.commit()

    def get_by_refresh_token(self, refresh_token: str):
        return self.db.query(UserSession).filter(UserSession.refresh_token == refresh_token).first()

    def delete(self, session_id: int):
        self.db.query(UserSession).filter(UserSession.id == session_id).delete()
        self.db.commit()

    def delete_by_user(self, user_id: int):
        self.clear_user_sessions(user_id)
