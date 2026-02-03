from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.response import Response
from app.schemas.cmp.vpc_schema import (VpcOut, VpcPage, VpcCreate, VpcList)

from app.services.cmp.vpc_service import VPCService
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user


def get_vpc_service(db: Session = Depends(get_cmp_db)):
    return VPCService(db)

router = APIRouter(
    prefix="/vpc",
    tags=["vpc"],
    dependencies=[Depends(require_user)]
)

# -------------------------------
# 下拉选择列表
# -------------------------------
@router.get("/list")
def list_vpcs(
    request: Request,
    provider_code: str = Query(None, description="云厂商code"),
    region_id: str = Query(None, description="区域 id"),
    service: VPCService = Depends(get_vpc_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    items = service.sync_vpcs(parent_id, provider_code, region_id)
    return Response.success(items)

@router.get('/page_list', response_model=VpcPage)
def list_page(
    request: Request,
    provider_code: Optional[str] = Query(None, description="云厂商code"),
    region_id: Optional[str] = Query(None, description="区域id"),
    resource_group_id: Optional[str] = Query(None, description="资源组"),
    vpc_name: Optional[str] = Query(None, description="vpc name"),
    page: int = Query(..., description="页码（从1开始）"),
    page_size: int = Query(..., description="每页条数"),
    service: VPCService = Depends(get_vpc_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    total, items = service.list_page(parent_id, page, page_size, provider_code, region_id, resource_group_id, vpc_name)
    return Response.success(VpcPage(page=page, pageSize=page_size, total=total, items=items))


@router.post("/create", response_model=VpcOut)
def create_vpc(
    request: Request,
    data: VpcCreate,
    service: VPCService = Depends(get_vpc_service)
):
    # user_id = request.state.user.get('user_id')
    vpc = service.create(request.state.user, data)
    return Response.success(vpc)

# 释放 VPC
@router.put("/release/{vpc_id}")
def release_vpc(
    vpc_id: int,
    service: VPCService = Depends(get_vpc_service)
):
    result = service.release(vpc_id)
    return Response.success(result)
