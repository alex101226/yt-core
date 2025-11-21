# app/services/auth_service.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.repositories.sso.user_repo import UserRepository
from app.repositories.sso.session_repo import SessionRepository
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, REFRESH_EXPIRE_DAYS
from app.schemas.sso.auth_schema import LoginRequest, TokenResponse, UserRegister
from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.models.sso.user import User
from app.services.sso.session_service import SessionService

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)

    def login(self, data: LoginRequest, ip: str = None, user_agent: str = None) -> TokenResponse:
        user = self.user_repo.get_by_username(data.username)
        if not user:
            raise ValueError("用户不存在")

        if not verify_password(data.password, user.hashed_password):
            raise ValueError("密码错误")

        # 单点登录：清除历史会话
        self.session_repo.clear_user_sessions(user.id)

        subject = {"user_id": user.id, "username": user.username}
        access = create_access_token(subject)
        refresh = create_refresh_token(subject)

        # 保存 refresh 到 DB（expires_at）
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
        self.session_repo.create(user.id, refresh, expires_at, ip=ip, user_agent=user_agent)

        return TokenResponse(access_token=access, refresh_token=refresh, token_type="bearer")

    def refresh(self, refresh_token: str) -> TokenResponse:
        # 找到 DB 中的会话
        session = self.session_repo.get_by_refresh_token(refresh_token)
        if not session:
            raise ValueError("无效的 refresh token")

        # 验证 refresh token 本身
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            # token 无效或过期
            self.session_repo.delete(session.id)
            raise ValueError("Refresh token 无效或已过期")

        # 生成新对 token（这次保持单点：不用创建新会话，只刷新 DB 过期时间）
        subject = {"user_id": payload.get("user_id"), "username": payload.get("username")}
        access = create_access_token(subject)
        new_refresh = create_refresh_token(subject)

        # 更新 DB：删除旧会话，创建新会话（确保单点）
        self.session_repo.clear_user_sessions(session.user_id)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_EXPIRE_DAYS)
        self.session_repo.create(session.user_id, new_refresh, expires_at, ip=session.ip, user_agent=session.user_agent)

        return TokenResponse(access_token=access, refresh_token=new_refresh, token_type="bearer")

    def logout(self, user_id: int):
        # 注销直接删除会话（使 refresh 无效）
        self.session_repo.clear_user_sessions(user_id)

    def register(self, data: UserRegister):
        # 检查重复
        exists = self.user_repo.get_by_username(data.username) \
                 or self.user_repo.get_by_email_or_mobile(data.email, data.mobile)
        if exists:
            raise BusinessException(code=ErrorCode.USER_ALREADY_EXISTS, message=Message.USER_ALREADY_EXISTS)

        user_data = data.model_dump()
        hashed_password = hash_password(user_data["password"])
        user_data.pop("password")
        user_data["hashed_password"] = hashed_password
        # 创建用户
        new_user = self.user_repo.create(User(**user_data))

        # 自动创建 refresh token 并返回 token
        tokens = SessionService(self.db).create_session_for_user(new_user)

        return tokens
