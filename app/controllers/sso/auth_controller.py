from fastapi import APIRouter, Depends, Response as FastAPIResponse
from sqlalchemy.orm import Session

from app.common.response import Response as ApiResponse
from app.common.dependencies import get_cmp_db, get_sso_db

from app.services.sso.auth_service import AuthService

from app.schemas.sso.auth_schema import (
LoginRequest, TokenResponse, RefreshTokenIn,
UserRegister, TokenOut, UserOut, LogoutRequest
)

ACCESS_TOKEN_EXPIRE_DAYS = 3000

def get_auth_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db),
):
  return AuthService(sso_db, cmp_db)

router = APIRouter(prefix="/auth", tags=["sso认证"])


# 清除cookie
def clear_auth_cookie(response: FastAPIResponse):
    response.delete_cookie("access_token", path="/")
    # response.delete_cookie("refresh_token", path="/", domain="你的域名")

#   登录
@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, response: FastAPIResponse, service: AuthService = Depends(get_auth_service)):

    result = service.login(data, response)

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
    service.logout(data.user_id, response)
    # clear_auth_cookie(response)
    # return ApiResponse.success(result)
    return {"code": 20000, "message": "已退出登录"}

# 注册
@router.post("/register", response_model=TokenOut)
def register(
    data: UserRegister,
    response: FastAPIResponse,
    service: AuthService = Depends(get_auth_service),
):
    result = service.register(data, response)
    result = {
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    }
    return ApiResponse.success(result, cookies={"access_token": result['access_token']})
