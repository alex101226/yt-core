from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user
from app.core.logger import logger

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate, EIPSave
from app.services.cmp.eip_service import EIPService

from app.enums.enums import EipStatus

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
    user_id = request.state.user.get('user_id')
    result = service.create_eip(user_id, data)
    return Response.success(result)

@router.get("/eip_page_list")
def get_eip_page_list(
    request: Request,
    page: int = Query(1, description="第几页"),
    page_size: int = Query(10, description="页码"),
    provider_code: Optional[str] = Query('aliyun', description="云厂商 code"),
    region_id: Optional[str] = Query('cn-qingdao', description="区域 id"),
    zone_id: Optional[str] = Query('cn-qingdao-b', description="可用区 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    eip_name: str = Query(None, description="eip名称"),
    public_ip: str = Query(None, description="ip地址"),
    server: EIPService = Depends(get_eip_service),
):
    user_id = request.state.user.get('user_id')
    result = server.get_eip_page_list(user_id, page, page_size, provider_code, region_id, zone_id, resource_group_id, eip_name, public_ip)
    return Response.success(result)

# eip解绑，绑定，释放
@router.post('/eip_action')
def eip_action(
    request: Request,
    data: EIPSave,
    service: EIPService = Depends(get_eip_service)
):
    user_id = request.state.user.get('user_id')
    result = service.eip_action(user_id, data)
    return Response.success(result)
