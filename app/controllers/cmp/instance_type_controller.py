from typing import List, Optional

from fastapi import APIRouter, Query, Depends
from app.common.response import Response

from app.services.cmp.dependencies import get_instance_type_service

from app.services.cmp.instance_type_service import InstanceTypeService

from app.schemas.cmp.instance_type_schema import InstanceTypeSearch

router = APIRouter(prefix="/instance_type", tags=["实例规则及计费"])

@router.get('/list', response_model=List[dict])
def instance_type_list(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    service: InstanceTypeService = Depends(get_instance_type_service)) -> List[dict]:
    items = service.list_instance_types(provider_code)
    return Response.success(items)


@router.get('/available_type', response_model=List[dict])
def available_type_list(
    search: InstanceTypeSearch = Depends(),
    service: InstanceTypeService = Depends(get_instance_type_service)) -> List[dict]:
    items = service.list_available_instance_types(search)
    return Response.success(items)