# app/controllers/cmp/subnet_controller.py
from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.services.cmp.dependencies import get_subnet_service
from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage
from app.common.response import Response

router = APIRouter(prefix="/subnet", tags=["子网管理"])

@router.post("/create", response_model=SubnetOut)
def create_subnet(
    data: SubnetCreate,
    service = Depends(get_subnet_service)
):
    result = service.create(data)
    return Response.success(result)

@router.get("/vpc_list/{vpc_id}", response_model=List[SubnetOut])
def list_subnets(
    vpc_id: str,
    service = Depends(get_subnet_service)
):
    items = service.list_by_vpc(vpc_id)
    return Response.success(items)

@router.post("/release/{subnet_id}", response_model=SubnetOut)
def release_subnet(
    subnet_id: str,
    cloud_provider_code: str,
    service = Depends(get_subnet_service)
):
    result = service.release(subnet_id, cloud_provider_code)
    return Response.success(result)


@router.get("/page_list", response_model=SubnetPage)
def page_subnets(
    cloud_provider_code: Optional[str] = Query(None),
    region_id: Optional[str] = Query(None),
    zone_id: Optional[str] = Query(None),
    vpc_id: Optional[str] = Query(None),
    resource_group_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    service = Depends(get_subnet_service)
):
    """分页查询子网"""
    return Response.success(
        service.page_subnets(
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            zone_id=zone_id,
            vpc_id=vpc_id,
            resource_group_id=resource_group_id,
            page=page,
            page_size=page_size
        )
    )
