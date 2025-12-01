# app/controllers/cmp/server_instance_controller.py
from fastapi import APIRouter, Depends, Request, Query
from typing import Optional, List
from enum import Enum

from sqlalchemy.orm import Session
from app.schemas.cmp.server_instance_schema import InstanceCreateSchema
from app.services.cmp.server_instance_service import InstanceService

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user


def get_server_instance_service(
   db: Session = Depends(get_cmp_db),
):
    return InstanceService(db)

class InstanceChargeType(str, Enum):
    POSTPAID = "PostPaid"
    PREPAID = "PrePaid"
    SPOT = "Spot"

router = APIRouter(prefix="/cloud_server", tags=["云服务器"], dependencies=[Depends(require_user)])
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3LCJleHAiOjE3NjQ1MTgyMzUsInR5cGUiOiJhY2Nlc3MifQ.1sMBe8a3xpsJv1_wZ22eL7NodfuZp7nLgGBsP2oP6nM
@router.post("/server_create")
def create_instance(
    data: InstanceCreateSchema,
    request: Request,
    service: InstanceService = Depends(get_server_instance_service)):

    user_id = request.state.user.get('user_id')
    payload = data.model_dump()
    payload['user_id'] = user_id

    instance = service.create_instance(payload)

    result = {
        "id": instance.id,
        "instance_name": instance.instance_name,
        "status": instance.status,
        "resource_group_id": instance.resource_group_id
    }
    return Response.success(result)


@router.get("/server_page_list")
def get_server_page_list(
    provider_code: Optional[str] = Query('aliyun', description="云厂商 code"),
    region_id: Optional[str] = Query('cn-qingdao', description="区域 id"),
    zone_id: Optional[str] = Query('cn-qingdao-b', description="可用区id"),
    resource_group_id: Optional[int] = Query(2, description="资源组id"),
    instance_id: Optional[str] =  Query(None, description="服务器实例id"),
    instance_name: Optional[str] =  Query(None, description="服务器实例名称"),
    instance_type: Optional[str] =  Query('ecs.g6.large', description="实例规格"),
    ip: Optional[str] =  Query('ecs.g6.large', description="ip"),
    status: Optional[int] = Query(1, description="服务器状态"),
    ssh_proxy_port: Optional[int] = Query(None, description="ssh 代理端口"),
    page: int = Query(1, description="分页"),
    page_size:int = Query(10, description="页码"),
    service: InstanceService = Depends(get_server_instance_service),
):
    result = service.server_list_page(
        provider_code, region_id, zone_id, resource_group_id, instance_id, instance_name,
        instance_type, ip, status, ssh_proxy_port, page, page_size
    )
    return Response.success(result)

