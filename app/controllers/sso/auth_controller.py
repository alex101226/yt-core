from fastapi import APIRouter, Depends, Response as FastAPIResponse
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.common.response import Response as ApiResponse
from app.common.dependencies import get_cmp_db, get_sso_db

from app.services.cmp.account_service import AccountService
from app.services.sso.auth_service import AuthService
# from app.services.sso.dependencies import get_auth_service

from app.schemas.sso.auth_schema import (
LoginRequest, TokenResponse, RefreshTokenIn,
UserRegister, TokenOut, UserOut, LogoutRequest
)

def get_auth_service( db: Session = Depends(get_sso_db)):
  return AuthService(db)

def get_account_service(
   db: Session = Depends(get_cmp_db),
):
    return AccountService(db)

router = APIRouter(prefix="/auth", tags=["sso认证"])


# 清除cookie
def clear_auth_cookie(response: FastAPIResponse):
    response.delete_cookie("access_token")
    # response.delete_cookie("refresh_token", path="/", domain="你的域名")

#   登录
@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, response: FastAPIResponse, service: AuthService = Depends(get_auth_service)):
    clear_auth_cookie(response)
    result = service.login(data)
    return ApiResponse.success(result, cookies={"access_token": result.access_token})

# 刷新token
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    r: RefreshTokenIn,
    service: AuthService = Depends(get_auth_service)
):
    result = service.refresh(r.refresh_token)
    return ApiResponse.success(result, cookies={"access_token": result.access_token})

#  注销：需要当前登录用户（access token）或若用 refresh 则也可实现。
@router.post("/logout")
def logout(
    data: LogoutRequest,
    response: FastAPIResponse,
    service: AuthService = Depends(get_auth_service)
):
    service.logout(data.user_id)
    clear_auth_cookie(response)
    # return ApiResponse.success(result)
    return {"code": 20000, "message": "已退出登录"}

# 注册
@router.post("/register", response_model=TokenOut)
def register(
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
    accountService: AccountService = Depends(get_account_service),
):
    result = service.register(data)
    accountService.account_create(result.user_id)
    result = {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }
    return ApiResponse.success(result, cookies={"access_token": result['access_token']})
