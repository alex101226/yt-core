from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_user
from app.common.dependencies import get_cmp_db
from app.common.response import Response

from app.services.cmp.container_image_service import ContainerImageService

from app.schemas.cmp.container_image_schema import ContainerImageCreate

# 云厂商，区域，云凭证, 资源组，计费方式, 集群名称，集群版本，集群规格，集群master实例数，实例规格，网络类型，VPC，IP子网，安全组，服务网段（Service CIDR）,集群删除保护,标签
def get_con_image_service(
   db: Session = Depends(get_cmp_db),
):
    return ContainerImageService(db)

router = APIRouter(
    prefix="/container_image",
    tags=["容器镜像服务"],
    dependencies=[Depends(require_user)]
)

#   创建容器镜像
@router.post("/con_image_create")
def image_create(
    data: dict,
    request: Request,
    service: ContainerImageService = Depends(get_con_image_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.image_create(request.state.user, data)
    return Response.success(result)

# 分页列表
@router.get("/con_image_page_list")
def con_image_page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    provider_code: str = Query(None, description="云厂商 code"),
    region_id: Optional[str] = Query(None, description="区域 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组 id"),
    repository_name: Optional[str] = Query(None, description="名称"),
    service: ContainerImageService = Depends(get_con_image_service),
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.con_image_page_list(parent_id, page, page_size, provider_code, region_id, resource_group_id, repository_name)
    return Response.success(result)
