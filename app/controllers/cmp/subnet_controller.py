# app/controllers/cmp/subnet_controller.py
from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.cmp.subnet_schema import SubnetCreate, SubnetOut, SubnetPage
from app.common.response import Response

from app.services.cmp.subnet_service import SubnetService
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

def get_subnet_service(db: Session = Depends(get_cmp_db)):
    return SubnetService(db)

router = APIRouter(
    prefix="/subnet",
    tags=["子网管理"],
    dependencies=[Depends(require_user)]
)

# 返回某个vpc列表下的子网
@router.get("/vpc_list/{vpc_id}", response_model=List[SubnetOut])
def list_subnets(
    vpc_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    service = Depends(get_subnet_service)
):
    result = service.vpc_id_by_subnet(vpc_id, page, page_size)
    return Response.success(result)

# 分页列表
@router.get("/page_list", response_model=SubnetPage)
def page_subnets(
    cloud_provider_code: Optional[str] = Query('aliyun', description="云厂商 code"),
    region_id: Optional[str] = Query('cn-beijing', description="区域id"),
    # zone_id: Optional[str] = Query(None),
    subnet_id: Optional[str] = Query(None, description="子网名称"),
    resource_group_id: Optional[int] = Query(1, description="默认资源组"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    service = Depends(get_subnet_service)
):
    result = service.page_subnets(
            cloud_provider_code=cloud_provider_code,
            region_id=region_id,
            subnet_id=subnet_id,
            resource_group_id=resource_group_id,
            page=page,
            page_size=page_size
        )
    """分页查询子网"""
    return Response.success(result)

# select的list
@router.get("/list", response_model=SubnetOut)
def list_subnets(
    vpc_id: int = Query(1, description="vpc id"),
    service = Depends(get_subnet_service)
):
    result = service.list_subnets(vpc_id)
    return Response.success(result)

# 创建
@router.post("/create", response_model=SubnetOut)
def create_subnet(
    data: SubnetCreate,
    request: Request,
    service = Depends(get_subnet_service)
):
    user_id = request.state.user.get('user_id')
    payload = data.model_dump()
    payload['user_id'] = user_id
    result = service.create(payload)
    return Response.success(result)

# 删除
@router.post("/release/{subnet_id}", response_model=SubnetOut)
def release_subnet(
    subnet_id: str,
    cloud_provider_code: str,
    service = Depends(get_subnet_service)
):
    result = service.subnet_release(subnet_id, cloud_provider_code)
    return Response.success(result)
