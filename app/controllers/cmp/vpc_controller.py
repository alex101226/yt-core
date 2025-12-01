from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.response import Response
from app.schemas.cmp.vpc_schema import (VpcOut, VpcPage, VpcCreate)

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
# 分页查询
# -------------------------------
@router.get("/list", response_model=VpcOut)
def list_vpcs(
    provider_code: str = Query('aliyun', description="云厂商code"),
    region_id: str = Query('cn-qingdao', description="区域 id"),
    service: VPCService = Depends(get_vpc_service)
):
    items = service.sync_vpcs(provider_code, region_id)
    return Response.success(items)

@router.get('/page_list', response_model=VpcPage)
def list_page(
        provider_code: str = Query('aliyun', description="云厂商code"),
        region_id: str = Query('cn-qingdao', description="区域id"),
        page: int = Query(1, ge=1, description="页码（从1开始）"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        service: VPCService = Depends(get_vpc_service)
):
    total, items = service.list_page(provider_code, region_id, page, page_size)
    return Response.success(VpcPage(page=page, pageSize=page_size, total=total, items=items))


@router.post("/create", response_model=VpcOut)
def create_vpc(
    data: VpcCreate,
    request: Request,
    service: VPCService = Depends(get_vpc_service)
):
    user_id = request.state.user.get('user_id')
    payload = data.model_dump()
    payload['user_id'] = user_id
    vpc = service.create(payload)
    return Response.success(vpc)

# 释放 VPC
@router.post("/release/{vpc_id}")
def release_vpc(
    vpc_id: int,
    service: VPCService = Depends(get_vpc_service)
):
    result = service.release(vpc_id)
    return Response.success(result)
