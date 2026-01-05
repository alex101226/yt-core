from fastapi import APIRouter, Depends, Request, Query

from app.core.dependencies import require_user

from app.common.response import Response
from app.core.logger import logger

from app.schemas.sso.auth_schema import UserOut

from app.services.sso.dependencies import get_user_service
from app.services.sso.user_service import UserService

router = APIRouter(
    prefix="/user",
    tags=["用户信息"],
    dependencies=[Depends(require_user)],
)

@router.get("/user_info", response_model=UserOut)
def me(request: Request, service: UserService = Depends(get_user_service)):
    user_id = request.state.user.get('user_id')
    # logger.info(f'获取用户id {user_id}')
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
