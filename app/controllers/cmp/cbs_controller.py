from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.services.cmp.cbs_service import CbsService
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate, CbsDiskReleaseSchema

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

def get_cbs_disk_service(db: Session = Depends(get_cmp_db)):
    return CbsService(db)

router = APIRouter(
    prefix="/cbs",
    tags=["云硬盘（CBS）"],
    dependencies=[Depends(require_user)],
)

#   cbs创建
@router.post("/cbs_create")
def cbs_create(
    data: CbsDiskCreate,
    request: Request,
    service: CbsService = Depends(get_cbs_disk_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.cbs_create(request.state.user, data.model_dump())
    return Response.success(result)

# 分页列表
@router.get("/cbs_page_list")
def cbs_page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    provider_code: str = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    zone_id: Optional[str] = Query(None, description="可用区 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    cbs_id: Optional[str] = Query(None, description="云硬盘名称"),
    service: CbsService = Depends(get_cbs_disk_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.cbs_page_list(parent_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, cbs_id)
    return Response.success(result)


# 释放
@router.post("/cbs_release")
def cbs_release(
    data: CbsDiskReleaseSchema,
    service: CbsService = Depends(get_cbs_disk_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.cbs_release(data.cbs_id)
    return Response.success(result)

# 卸载
@router.post("/cbs_uninstall")
def cbs_uninstall(
    data: CbsDiskReleaseSchema,
    service: CbsService = Depends(get_cbs_disk_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.cbs_uninstall(data.cbs_id)
    return Response.success(result)