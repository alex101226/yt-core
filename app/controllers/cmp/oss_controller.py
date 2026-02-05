from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.schemas.cmp.oss_schema import OssCreate
from app.services.cmp.oss_service import OssBucketService

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

def get_oss_service(db: Session = Depends(get_cmp_db)):
    return OssBucketService(db)

router = APIRouter(
    prefix="/oss",
    tags=["对象存储（OSS）"],
    dependencies=[Depends(require_user)],
)

#   oss创建
@router.post("/oss_create")
def cbs_create(
    request: Request,
    data: OssCreate,
    service: OssBucketService = Depends(get_oss_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.oss_create(request.state.user, data)
    return Response.success(result)


# 分页列表
@router.get("/oss_page_list")
def oss_page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    provider_code: str = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    bucket_name: Optional[str] = Query(None, description="oss存储痛名称"),
    permission: Optional[str] = Query(None, description="访问权限：private-read-write / public-read-write / public-read-private-write"),
    service: OssBucketService = Depends(get_oss_service),
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.oss_page_list(parent_id, page, page_size, provider_code, region_id, resource_group_id, bucket_name, permission)
    return Response.success(result)

# 释放
@router.delete("/release/{oss_id}")
def delete_gpfs(
    oss_id: int,
    service: OssBucketService = Depends(get_oss_service),
):
    result = service.release(oss_id)
    return Response.success(result)

