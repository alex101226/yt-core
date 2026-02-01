from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.schemas.cmp.bare_metal_instance_schema import BareMetalInstanceCreate
from app.services.cmp.bare_metal_instance_service import BareMetalInstanceService

def get_bare_service(
   db: Session = Depends(get_cmp_db),
):
    return BareMetalInstanceService(db)

router = APIRouter(prefix="/bare_metal_instance", tags=["裸金属"], dependencies=[Depends(require_user)])

# 创建裸金属
@router.post("/bare_metal_create")
def create_instance(
    request: Request,
    data: BareMetalInstanceCreate,
    service: BareMetalInstanceService = Depends(get_bare_service)):

    # user_id = request.state.user.get('user_id')
    instance = service.bare_metal_instance_create(request.state.user, data)

    return Response.success(instance)


@router.get("/bare_metal_page_list")
def get_bare_metal_page_list(
    request: Request,
    page: int = Query(..., description="当前页码"),
    page_size: int = Query(..., description="一页多少条数据"),
    provider_code: Optional[str] = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    zone_id: Optional[str] = Query(None, description="可用区 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    instance_id: Optional[str] = Query(None, description="创建的裸金属的实例id， 字段=instance_id"),
    instance_name: Optional[str] = Query(None, description="创建的裸金属的实例name，字段=instance_name"),
    instance_type_id: Optional[str] = Query(None, description="实例规格 ID，如 ecs.g6.large"),
    public_ip: Optional[str] = Query(None, description="分配的公网ip，字段=public_ip"),
    status: Optional[str] = Query(None, description="裸金属状态，查字典表的item_type=BAREMETAL_INSTANCE_STATUS"),
    ssh_proxy_port: Optional[int] = Query(None, description="ssh代理端口，字段=ssh_proxy_port"),
    service: BareMetalInstanceService = Depends(get_bare_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    instance = service.bare_metal_page_list(
        parent_id, page, page_size, provider_code, region_id, zone_id, resource_group_id,
        instance_id, instance_name, instance_type_id, public_ip, status, ssh_proxy_port
    )
    return Response.success(instance)
