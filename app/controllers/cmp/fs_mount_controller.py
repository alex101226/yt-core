from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

from app.services.cmp.fs_mount_service import FileMountService
from app.schemas.cmp.fs_mount_schema import FileSystemMountCreate

def get_mount_service(db: Session = Depends(get_cmp_db)):
    return FileMountService(db)

router = APIRouter(
    prefix="/fs_mount",
    tags=["文件挂载点"],
    dependencies=[Depends(require_user)],
)
#   oss创建
@router.post("/mount_create")
def cbs_create(
    request: Request,
    data: FileSystemMountCreate,
    service: FileMountService = Depends(get_mount_service)
):
    user_id = request.state.user.get('user_id')
    result = service.fs_mount_create(user_id, data)
    return Response.success(result)

#   oss创建
@router.get("/mount_page_list")
def cbs_create(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    mount_type: str = Query(..., description="文件挂载类型, gpfs/cephfs"),
    provider_code: Optional[str] = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    zone_id: Optional[str] = Query(None, description="可用区 id"),
    mount_name: Optional[str] = Query(None, description="挂载点 名称"),
    service: FileMountService = Depends(get_mount_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')

    result = service.fs_mount_page_list(page, page_size, parent_id, mount_type, provider_code, region_id, zone_id, mount_name)
    return Response.success(result)