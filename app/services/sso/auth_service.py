# app/services/auth_service.py
from fastapi import Response as FastAPIResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, \
    REFRESH_EXPIRE_DAYS

from app.common.status_code import ErrorCode
from app.common.messages import Message
from app.common.exceptions import BusinessException
from app.core.logger import logger

from app.services.cmp.account_service import AccountService

from app.models.sso.session import UserSession

from app.repositories.sso.user_repo import UserRepository
from app.repositories.sso.session_repo import SessionRepository
from app.schemas.sso.auth_schema import (
LoginRequest, TokenResponse, UserRegister
)

ACCESS_TOKEN_EXPIRE_DAYS = 3000

class AuthService:
    def __init__(self, db: Session, cmp_db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.session_repo = SessionRepository(db)
        self.account_service = AccountService(cmp_db)

    # 登录
    def login(
        self,
        data: LoginRequest,
        response: FastAPIResponse,
        ip = None,
        user_agent = None
    ) -> TokenResponse:
        user = self.user_repo.get_by_username(data.username)

        if not user:
            raise BusinessException(code=ErrorCode.USER_NOT_FOUND, message=Message.USER_NOT_FOUND)

        if not verify_password(data.password, user.hashed_password):
            raise BusinessException(code=ErrorCode.PASSWORD_INCORRECT, message=Message.PASSWORD_INCORRECT)
        # 单点登录：清除历史会话
        response.delete_cookie("access_token", path="/")
        self.session_repo.clear_user_sessions(user.id)

        subject = {"user_id": user.id, "username": user.username, "parent_id": user.parent_id}
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
        # 下发 cookie：注意 max_age / expires / httponly / secure
        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,  # HTTPS 环境必须
            samesite="lax",  # 同域名可选 laks, 跨域需 None
            max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 秒
            path="/",
        )
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            user_id=user.id,
        )

    # 注册
    def register(self, data: UserRegister, response: FastAPIResponse,) -> TokenResponse:
        # 检查重复
        exists = self.user_repo.get_by_username(data.username)

        if exists:
            raise BusinessException(code=ErrorCode.USER_ALREADY_EXISTS, message=Message.USER_ALREADY_EXISTS)

        payload = {
            "nickname": data.nickname,
            "username": data.username,
            "hashed_password": hash_password(data.password),
            "role_code": data.role_code or "admin",
            "parent_id": 0,
            "user_type": "internal" if (data.role_code == "root") else "tenant",
        }

        # 创建用户
        new_user = self.user_repo.create(payload)
        self.account_service.account_create(new_user)

        # 单点登录：清除历史会话
        self.session_repo.clear_user_sessions(new_user.id)

        subject = {"user_id": new_user.id, "username": new_user.username, "parent_id": new_user.parent_id}

        access = create_access_token(subject)
        refresh = create_refresh_token(subject)

        # 保存 refresh 到 DB（expires_at）
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS)

        # 自动创建 refresh token 并返回 token
        session_model = UserSession(
            user_id=new_user.id,
            refresh_token=refresh,
            expires_at=expires_at,
        )
        self.session_repo.create(session_model)

        self.db.commit()
        self.db.refresh(new_user)

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=True,  # HTTPS 环境必须
            samesite="lax",  # 同域名可选 laks, 跨域需 None
            max_age=ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 秒
            path="/",
        )

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            user_id=new_user.id
        )

    # 刷新token
    def refresh(self, data) -> TokenResponse:
        # 找到 DB 中的会话
        session = self.session_repo.get_by_refresh_token(data.refresh_token)
        if not session:
            raise BusinessException(code=ErrorCode.LOGIN_FAILED, message=Message.PASSWORD_INCORRECT)

            # 2. 检查 refresh_token 是否过期
        if session.expires_at < datetime.now(timezone.utc):
            self.session_repo.delete(session.id)
            raise BusinessException(code=ErrorCode.LOGIN_FAILED, message="refresh token 已过期，请重新登录")

            # 3. 生成新的 access_token（refresh 不变）
        subject = {"user_id": session.user_id}
        access = create_access_token(subject)
        return TokenResponse(access_token=access, refresh_token=data.refresh_token, token_type="bearer")

    # 退出登录
    def logout(self, user_id: int, response: FastAPIResponse):
        if not user_id:
            return False
        self.session_repo.clear_user_sessions(user_id)
        response.delete_cookie("access_token", path="/")
        return True
