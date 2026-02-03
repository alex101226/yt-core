from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user
from app.core.logger import logger

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPSave
from app.services.cmp.eip_service import EIPService

def get_eip_service(db: Session = Depends(get_cmp_db)):
    return EIPService(db)

router = APIRouter(
    prefix="/eip",
    tags=["弹性公网"],
    dependencies=[Depends(require_user)]
)

#   创建eip
@router.post("/eip_create")
def create_eip(
    data: EIPCreate,
    request: Request,
    service: EIPService = Depends(get_eip_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.create_eip(request.state.user, data)
    return Response.success(result)

@router.get("/eip_page_list")
def get_eip_page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    provider_code: Optional[str] = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    zone_id: Optional[str] = Query(None, description="可用区 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    eip_name: str = Query(None, description="eip名称"),
    public_ip: str = Query(None, description="ip地址"),
    server: EIPService = Depends(get_eip_service),
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = server.get_eip_page_list(parent_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, eip_name, public_ip)
    return Response.success(result)

# eip解绑   UNBINDING
@router.put('/eip_unbind/{eip_id}')
def eip_unbind(
    eip_id: int,
    service: EIPService = Depends(get_eip_service)
):
    result = service.eip_unbind(eip_id)
    return Response.success(result)

# eip绑定
@router.post('/bind')
def eip_bind(
    data: EIPSave,
    service: EIPService = Depends(get_eip_service)
):
    result = service.eip_bind(data)
    return Response.success(result)

# eip释放
@router.put('/eip_release/{eip_id}')
def eip_release(
    eip_id: int,
    service: EIPService = Depends(get_eip_service)
):
    result = service.eip_release(eip_id)
    return Response.success(result)
