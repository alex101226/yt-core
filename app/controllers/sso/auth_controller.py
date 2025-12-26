from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.common.response import Response
from app.common.dependencies import get_cmp_db, get_sso_db

from app.services.cmp.account_service import AccountService
from app.services.sso.auth_service import AuthService
# from app.services.sso.dependencies import get_auth_service

from app.schemas.sso.auth_schema import (
LoginRequest, TokenResponse, RefreshTokenIn,
UserRegister, TokenOut, UserOut, LogoutRequest
)

def get_auth_service(
   db: Session = Depends(get_sso_db),
):
    return AuthService(db)

def get_account_service(
   db: Session = Depends(get_cmp_db),
):
    return AccountService(db)

router = APIRouter(prefix="/auth", tags=["sso认证"])

#   登录
@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    result = service.login(data)
    return Response.success(result)

# 刷新token
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(r: RefreshTokenIn, service: AuthService = Depends(get_auth_service)):
    result = service.refresh(r.refresh_token)
    return Response.success(result)

#  注销：需要当前登录用户（access token）或若用 refresh 则也可实现。
@router.post("/logout")
def logout(
    data: LogoutRequest,
    service: AuthService = Depends(get_auth_service)
):
    service.logout(data.user_id)
    return Response.success(True)

# 注册
@router.post("/register", response_model=TokenOut)
def register(
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
    accountService: AccountService = Depends(get_account_service),
):
    result = service.register(data)
    accountService.account_create(result.user_id)
    return Response.success({
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    })
