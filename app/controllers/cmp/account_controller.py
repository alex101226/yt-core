from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.account_service import AccountService
from app.schemas.cmp.account_schema import AccountCreate

def get_account_service(
   db: Session = Depends(get_cmp_db),
):
    return AccountService(db)

router = APIRouter(prefix="/account", tags=["资金账户"], dependencies=[Depends(require_user)])

# 查看用户账户信息
@router.get('/account_info')
def account_exists(request: Request, service: AccountService = Depends(get_account_service)):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    result = service.account_exists(parent_id)
    return Response.success(result)

# 开通账户
# @router.post('/account_create')
# def account_create(request: Request, service: AccountCreate = Depends(get_account_service)):
#     # user_id = request.state.user.get('user_id')
#     result = service.account_create(request.state.user)
#     return Response.success(result)

# 用户充值
@router.post('/recharge')
def recharge(
    request: Request,
    data: AccountCreate,
    service: AccountService = Depends(get_account_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.account_recharge(request.state.user, data)
    return Response.success(result)

