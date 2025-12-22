# app/services/auth_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, \
    REFRESH_EXPIRE_DAYS

from app.models.sso.user import User
from app.models.sso.session import UserSession
from app.services.sso.session_service import SessionService

from app.repositories.sso.user_repo import UserRepository
from app.repositories.sso.session_repo import SessionRepository
from app.schemas.sso.auth_schema import LoginRequest, TokenResponse, UserRegister

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException
from app.core.logger import logger

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    def login(self, data: LoginRequest, ip: str = None, user_agent: str = None) -> TokenResponse:
        user = self.user_repo.get_by_username(data.username)

        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        if not verify_password(data.password, user.hashed_password):
            raise BusinessException(code=ErrorCode.PASSWORD_INCORRECT, message=Message.PASSWORD_INCORRECT)


        # 单点登录：清除历史会话
        self.session_repo.clear_user_sessions(user.id)

        subject = {"user_id": user.id, "username": user.username}
        access = create_access_token(subject)
        refresh = create_refresh_token(subject)

        # 保存 refresh 到 DB（expires_at）
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
        session_model = UserSession(
            user_id=user.id,
            refresh_token=refresh,
            expires_at=expires_at,
            ip=ip,
            user_agent=user_agent
        )
        # tokens = SessionService(self.db).create_session_for_user(user)
        self.session_repo.create(session_model)

        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    def refresh(self, refresh_token: str) -> TokenResponse:
        # 找到 DB 中的会话
        session = self.session_repo.get_by_refresh_token(refresh_token)
        if not session:
            raise BusinessException(code=ErrorCode.LOGIN_FAILED, message=Message.PASSWORD_INCORRECT)

            # 2. 检查 refresh_token 是否过期
        if session.expires_at < datetime.utcnow():
            self.session_repo.delete(session.id)
            raise BusinessException(code=ErrorCode.LOGIN_FAILED, message="refresh token 已过期，请重新登录")

            # 3. 生成新的 access_token（refresh 不变）
        subject = {"user_id": session.user_id}
        access = create_access_token(subject)

        return TokenResponse(access_token=access, refresh_token=refresh_token, token_type="bearer")

    def logout(self, user_id: int):
        if not user_id:
            return False
        # 注销直接删除会话（使 refresh 无效）
        self.session_repo.clear_user_sessions(user_id)

    def register(self, data: UserRegister):
        # 检查重复
        exists = self.user_repo.get_by_username(data.username) or self.user_repo.get_by_email(data.email)

        if exists:
            raise BusinessException(code=ErrorCode.USER_ALREADY_EXISTS, message=Message.USER_ALREADY_EXISTS)

        payload = {
            **data.model_dump(),
            "hashed_password": hash_password(data.password)
        }
        payload.pop('password')

        # 创建用户
        new_user = self.user_repo.create(payload)

        # 单点登录：清除历史会话
        self.session_repo.clear_user_sessions(new_user.id)

        subject = {"user_id": new_user.id, "username": new_user.username}

        access = create_access_token(subject)
        refresh = create_refresh_token(subject)

        # 保存 refresh 到 DB（expires_at）
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)
        session_model = UserSession(
            user_id=new_user.id,
            refresh_token=refresh,
            expires_at=expires_at,
        )
        # tokens = SessionService(self.db).create_session_for_user(user)
        self.session_repo.create(session_model)
        # 自动创建 refresh token 并返回 token
        # tokens = SessionService(self.db).create_session_for_user(new_user)

        self.db.commit()
        self.db.refresh(new_user)
        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")