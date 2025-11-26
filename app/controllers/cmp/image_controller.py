from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, Query
from app.services.cmp.dependencies import get_image_service
from app.services.cmp.image_service import ImageService
from app.common.response import Response


router = APIRouter(prefix="/image", tags=["系统镜像"])
@router.get("/list", response_model=List[dict])
def images_list(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-beijing', description="区域 id"),
    instance_type_id: str = Query('ecs.c2.medium', description="规格实例id"),
    architecture: str = Query('x86_64', description="CPU 架构：x86 或 arm"),
    service: ImageService = Depends(get_image_service)) -> List[dict]:
    items = service.list(provider_code, region_id, instance_type_id, architecture)
    return Response.success(items)