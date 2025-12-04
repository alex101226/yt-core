from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.response import Response

from app.services.cmp.cbs_service import CbsService
from app.schemas.cmp.cbs_disk_schema import CbsDiskCreate

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.enums.enums import DiskType, DiskCategory, ChargeType, DiskStatus

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
    user_id = request.state.user.get('user_id')
    result = service.cbs_create(user_id, data)
    return Response.success(result)

# 分页列表
@router.post("/cbs_page_list")
def cbs_page_list(
    page: int = Query(1, description="第几页"),
    page_size: int = Query(1, description="页码"),
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: Optional[str] = Query('cn-qingdao', description="区域 id"),
    zone_id: Optional[str] = Query('cn-qingdao-b', description="可用区 id"),
    resource_group_id: Optional[int] = Query(None, description="资源组 id"),
    cbs_id: Optional[str] = Query(None, description="云硬盘名称"),
    tag: Optional[List[str]] = Query(None, description="标签"),
    service: CbsService = Depends(get_cbs_disk_service)
):
    result = service.cbs_page_list(page, page_size, provider_code, region_id, zone_id, resource_group_id, cbs_id, tag)
    return Response.success(result)