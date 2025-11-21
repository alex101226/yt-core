from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db
from app.schemas.sso.auth_schema import LoginRequest, TokenResponse, LoginResponse, UserRegister, TokenOut, UserOut
from app.services.sso.auth_service import AuthService
from app.services.sso.dependencies import get_user_service
from app.common.response import Response
from app.core.dependencies import get_current_user_optional
from app.common.response import Response


router = APIRouter(prefix="/auth", tags=["sso认证"])

#   登录
@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, service: AuthService = Depends(get_user_service)):
    result = service.login(data)
    return Response.success(result)


# @router.post("/refresh", response_model=TokenResponse)
# def refresh(r: RefreshRequest, db: Session = Depends(get_sso_db)):
#     svc = AuthService(db)
#     try:
#         return svc.refresh(r.refresh_token)
#     except ValueError as e:
#         raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
def logout(user = Depends(get_current_user_optional), db: Session = Depends(get_sso_db)):
    """
    注销：需要当前登录用户（access token）或若用 refresh 则也可实现。
    get_current_user_optional 返回 None 或 payload dict
    """
    if not user:
        raise HTTPException(401, "Not authenticated")
    svc = AuthService(db)
    svc.logout(user["user_id"])
    return {"ok": True}

@router.get("/me")
def me(user = Depends(get_current_user_optional)):
    if not user:
        raise HTTPException(401, "Not authenticated")
    return {"user_id": user["user_id"], "username": user["username"]}


@router.post("/register", response_model=TokenOut)
def register(data: UserRegister, service: AuthService = Depends(get_user_service)):
    result = service.register(data)
    Response.success({
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "user": UserOut.model_validate(result["user"])
    })
