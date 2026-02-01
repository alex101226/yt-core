from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.common.response import Response
from app.core.logger import logger

from app.services.sso.user_service import UserService
from app.common.dependencies import get_sso_db
from app.common.dependencies import get_cmp_db

from app.schemas.sso.auth_schema import UserOut, UserRegister

def get_user_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db)
):
  return UserService(sso_db, cmp_db)

router = APIRouter(
    prefix="/user",
    tags=["用户信息"],
    dependencies=[Depends(require_user)],
)

# 用户信息
@router.get("/user_info")
def me(
    request: Request,
    service: UserService = Depends(get_user_service),
):
    user_id = request.state.user.get('user_id')
    user = service.user_info(user_id)
    return Response.success(user)


# 用户列表
@router.get("/user_page_list")
def user_page_list(
    page: int = Query(..., description="当前页码"),
    page_size: int = Query(..., description="一页多少条数据"),
    nickname: str = Query(None, description="昵称"),
    username: str = Query(None, description="用户账号"),
    service: UserService = Depends(get_user_service)
):
    result = service.user_page_list(page, page_size, nickname, username)
    return Response.success(result)

# 创建用户
@router.post('/user_create')
def user_create(
    request: Request,
    data: UserRegister,
    service: UserService = Depends(get_user_service),
):
    user_id = request.state.user.get('user_id')
    result = service.user_create(user_id, data)
    return Response.success(result)

# 删除用户
@router.delete("/delete")
def user_delete(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    result = service.user_delete(user_id)
    return Response.success(result)


# 返回用户的账号数量
@router.get("/user_count")
def user_update(
    request: Request,
    service: UserService = Depends(get_user_service)
):
    result = service.user_count(request.state.user)
    return Response.success(result)
