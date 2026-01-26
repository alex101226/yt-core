from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.load_service import LoadBalancerService
from app.schemas.cmp.load_schema import (
LoadBalancerCreate, LoadBalancerACLCreate, LoadCertificateCreate
)

def get_load_service(
   db: Session = Depends(get_cmp_db),
):
    return LoadBalancerService(db)

router = APIRouter(prefix="/load", tags=["负载均衡"], dependencies=[Depends(require_user)])

# ------------------- 负载均衡 -> 实例 接口 -------------------

# 创建负载均衡
@router.post("/instance/create")
def load_create(
    request: Request,
    data: LoadBalancerCreate,
    service: LoadBalancerService = Depends(get_load_service)
):
    result = service.create_load_balancer(request.state.user, data)
    return Response.success(result)

# 列表
@router.get("/instance/page_list")
def get_instance_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    provider_code: Optional[str] = Query(None, description="云厂商"),
    region_id: Optional[str] = Query(None, description="区域id"),
    resource_group_id: Optional[str] = Query(None, description="资源组"),
    lb_name: Optional[str] = Query(None, description="实例名称"),
    service: LoadBalancerService = Depends(get_load_service)
):
    user_id = request.state.user['user_id']
    result = service.instance_page_list(
        user_id, page, page_size, provider_code, region_id, resource_group_id, lb_name
    )
    return Response.success(result)

# ------------------- 负载均衡-> 访问控制 接口 -------------------

# 创建访问控制
@router.post("/acl/create")
def create_acl(
    request: Request,
    data: LoadBalancerACLCreate,
    service: LoadBalancerService = Depends(get_load_service)
):
    result = service.create_acl(request.state.user, data)
    return Response.success(result)

# ACL 列表
@router.get("/acl/page_list")
def acl_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    provider_code: Optional[str] = Query(None, description="云厂商"),
    region_id: Optional[str] = Query(None, description="区域"),
    resource_group_id: Optional[int] = Query(None, description="资源组"),
    name: Optional[str] = Query(None, description="ACL 名称"),
    service: LoadBalancerService = Depends(get_load_service),
):
    user_id = request.state.user["user_id"]
    result = service.acl_page_list(
        user_id=user_id,
        page=page,
        page_size=page_size,
        provider_code=provider_code,
        region_id=region_id,
        resource_group_id=resource_group_id,
        name=name,
    )
    return Response.success(result)

# ------------------- 负载均衡-> 证书 接口 -------------------
# 创建负载均衡证书
@router.post("/certificate/create")
def certificate_create(
    request: Request,
    data: LoadCertificateCreate,
    service: LoadBalancerService = Depends(get_load_service)
):
    result = service.create_certificate(request.state.user, data)
    return Response.success(result)


# 分页获取证书列表
@router.get("/certificate/page_list")
def certificate_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    provider_code: Optional[str] = Query(None, description="云厂商"),
    region_id: Optional[str] = Query(None, description="区域id"),
    resource_group_id: Optional[int] = Query(None, description="资源组"),
    service: LoadBalancerService = Depends(get_load_service)
):
    user_id = request.state.user['user_id']

    result = service.certificate_page_list(
        user_id=user_id,
        page=page,
        page_size=page_size,
        provider_code=provider_code,
        region_id=region_id,
        resource_group_id=resource_group_id,
    )

    return Response.success(result)