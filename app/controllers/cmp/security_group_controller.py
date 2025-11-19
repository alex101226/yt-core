from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.schemas.cmp.security_group_schema import SecurityGroupSearch, SecurityGroupPage, SecurityGroupOut, SecurityGroupCreate
from app.services.cmp.security_group_service import SecurityGroupService
from app.services.cmp.dependencies import get_security_service
from app.common.response import Response

router = APIRouter(prefix="/security_groups", tags=["安全组"])

@router.get("/list_page", response_model=SecurityGroupPage)
def list_security_groups(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-qingdao', description="区域 id"),
    resource_group_id: Optional[int] = Query(None),
    name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    service: SecurityGroupService = Depends(get_security_service),
):
    filters = SecurityGroupSearch(
        cloud_provider_code=provider_code,
        region_id=region_id,
        resource_group_id=resource_group_id,
        security_name=name,
        page=page,
        page_size=page_size
    )
    items =  service.list(filters)
    return Response.success(items)
    # return service.list(filters)



@router.post("/create", response_model=SecurityGroupOut)
def create_security_group(
    body: SecurityGroupCreate,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.create(body)
    return Response.success(result)


@router.post("/release")
def release_security_group(
    groud_id: str,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.release(groud_id)
    return Response.success(result)
