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

# def get_auth_service(db: Session = Depends(get_sso_db), response: Response = Depends()):
#     return AuthService(db=db, response=response)

def get_account_service(
   db: Session = Depends(get_cmp_db),
):
    return AccountService(db)

router = APIRouter(prefix="/auth", tags=["sso认证"])

# 设置cookie
def set_cookie_done(res: FastAPIResponse, key: str, value: str, domain: str):
    payload = {
        "key": key,
        "value": value,
        "httponly": True,
        "secure": False,
        "samesite": "None",
        "path": "/",
        "domain": domain,
        "max_age": 300000
    }
    res.set_cookie(**payload)
    return payload

# 清除cookie
def clear_auth_cookie(response: FastAPIResponse):
    response.delete_cookie("access_token", path="/", domain="122.51.216.157")
    # response.delete_cookie("refresh_token", path="/", domain="你的域名")

#   登录
@router.post("/login", response_model=TokenOut)
def login(data: LoginRequest, response: FastAPIResponse, service: AuthService = Depends(get_auth_service)):
    # result = service.login(data, response)
    # c = set_cookie_done(response, "access_token", result.access_token, data.domain)
    result = service.login(data, response)
    return ApiResponse.success(result, cookies={"access_token": result.access_token})

# 刷新token
@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    r: RefreshTokenIn,
    response: FastAPIResponse,
    service: AuthService = Depends(get_auth_service)
):
    result = service.refresh(r.refresh_token, response)
    return ApiResponse.success(result)

#  注销：需要当前登录用户（access token）或若用 refresh 则也可实现。
@router.post("/logout")
def logout(
    data: LogoutRequest,
    response: FastAPIResponse,
    service: AuthService = Depends(get_auth_service)
):
    result = service.logout(response, data.user_id)
    return ApiResponse.success(result)

# 注册
@router.post("/register", response_model=TokenOut)
def register(
    data: UserRegister,
    response: FastAPIResponse,
    service: AuthService = Depends(get_auth_service),
    accountService: AccountService = Depends(get_account_service),
):
    result = service.register(data, response)
    accountService.account_create(result.user_id)
    return ApiResponse.success({
        "access_token": result.access_token,
        "refresh_token": result.refresh_token,
        "token_type": "bearer",
    })
