from typing import List

from fastapi import APIRouter, Depends, Path, Query

from app.common.response import Response
from app.schemas.cmp.vpc_schema import (VpcOut, VpcPage)

from app.services.cmp.dependencies import get_vpc_service
from app.services.cmp.vpc_service import VPCService

router = APIRouter(prefix="/vpc", tags=["vpc"])

# -------------------------------
# 分页查询
# -------------------------------
@router.get("/list", response_model=VpcOut)
def list_vpcs(
    provider_code: str = Query('aliyun'),
    region_id: str = Query('cn-qingdao'),
    service: VPCService = Depends(get_vpc_service)
):
    items = service.sync_vpcs(provider_code, region_id)
    return Response.success(items)

@router.get('/pageList', response_model=VpcPage)
def list_page(
        provider_code: str = Query('aliyun', description="云厂商code"),
        region_id: str = Query('cn-qingdao', description="区域id"),
        page: int = Query(1, ge=1, description="页码（从1开始）"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        service: VPCService = Depends(get_vpc_service)
):
    total, items = service.list_page(provider_code, region_id, page, page_size)
    return Response.success(VpcPage(page=page, pageSize=page_size, total=total, items=items))
