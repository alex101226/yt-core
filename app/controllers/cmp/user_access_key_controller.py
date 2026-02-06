from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.common.response import Response
from app.common.dependencies import get_cmp_db

from app.services.cmp.user_access_key_service import UserAccessKeyService
from app.schemas.cmp.user_access_key_schema import CreateUserAccessKeySchema

router = APIRouter(
    prefix="/access",
    tags=["用户密钥"],
    dependencies=[Depends(require_user)]
)

def get_access_service(db: Session = Depends(get_cmp_db)):
    return UserAccessKeyService(db)

# 创建
@router.post("/create")
def create_certificate(
    data: CreateUserAccessKeySchema,
    request: Request,
    service: UserAccessKeyService = Depends(get_access_service)
):
    obj = service.create_access_key(request.state.user, data)
    return Response.success(obj)

# 列表
@router.get('/page_list')
def access_key_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    service: UserAccessKeyService = Depends(get_access_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')

    result = service.access_key_page_list(parent_id, page, page_size)
    return Response.success(result)

# 禁用
@router.put('/disable/{access_key_id}')
def disable(
    access_key_id: int,
    service: UserAccessKeyService = Depends(get_access_service)
):
    result = service.set_disabled(access_key_id)
    return Response.success(result)

# 删除
@router.delete('/delete/{access_key_id}')
def delete(
    access_key_id: int,
    service: UserAccessKeyService = Depends(get_access_service)
):
    result = service.release(access_key_id)
    return Response.success(result)