from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

from app.services.cmp.gpfs_service import GPFSService
from app.schemas.cmp.gpfs_schema import GPFSOut, GPFSCreate, GPFSPage

def get_gpfs_service(db: Session = Depends(get_cmp_db)):
    return GPFSService(db)

router = APIRouter(
    prefix="/gpfs",
    tags=["gpfs 存储"],
    dependencies=[Depends(require_user)],
)

#   gpfs创建
@router.post("/cephfs_create")
def gpfs_create(
    request: Request,
    data: GPFSCreate,
    service: GPFSService = Depends(get_gpfs_service)
):
    user_id = request.state.user.get('user_id')
    result = service.gpfs_create(user_id, data)
    return Response.success(result)

# 分页列表
@router.post("/gpfs_page_list")
def gpfs_page_list(
    request: Request,
    page: int = Query(1, description="第几页"),
    page_size: int = Query(10, description="页码"),
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: Optional[str] = Query('cn-qingdao', description="区域 id"),
    zone_id: Optional[str] = Query('cn-qingdao-b', description="可用区 id"),
    storage_type: Optional[str] = Query(None, description="存储类型"),
    fs_name: Optional[str] = Query(None, description="名称"),
    service: GPFSService = Depends(get_gpfs_service),
):
    user_id = request.state.user.get('user_id')
    result = service.gpfs_page_list(user_id, page, page_size, provider_code, region_id, zone_id, storage_type, fs_name)
    return Response.success(result)

