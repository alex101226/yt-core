from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.schemas.cmp.cephfs_file_schema import CephfsCreate
from app.services.cmp.cephfs_file_service import CephfsFileService

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

def get_cephfs_service(db: Session = Depends(get_cmp_db)):
    return CephfsFileService(db)

router = APIRouter(
    prefix="/cephfs",
    tags=["cephfs 存储"],
    dependencies=[Depends(require_user)],
)

#   oss创建
@router.post("/cephfs_create")
def cephfs_create(
    request: Request,
    data: CephfsCreate,
    service: CephfsFileService = Depends(get_cephfs_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.cephfs_file_create(request.state.user, data)
    return Response.success(result)


# 分页列表
@router.get("/cephfs_page_list")
def cephfs_page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    provider_code: str = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    storage_type: Optional[str] = Query(None, description="存储类型"),
    fs_name: Optional[str] = Query(None, description="名称"),
    service: CephfsFileService = Depends(get_cephfs_service),
):
    user_id = request.state.user.get('user_id')
    result = service.cephfs_page_list(user_id, page, page_size, provider_code, region_id, resource_group_id, storage_type, fs_name)
    return Response.success(result)


# list
@router.get("/cephfs_list")
def cephfs_list(
    request: Request,
    region_id: str = Query(..., description="区域的id"),
    status: Optional[str] = Query(None, description="状态"),
    service: CephfsFileService = Depends(get_cephfs_service),
):
    user_id = request.state.user.get('user_id')
    result = service.cephfs_list(user_id, region_id, status)
    return Response.success(result)

