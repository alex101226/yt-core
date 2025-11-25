from typing import List

from fastapi import APIRouter, Depends, Query
from app.services.cmp.dependencies import get_image_service
from app.services.cmp.image_service import ImageService
from app.common.response import Response

router = APIRouter(prefix="/image", tags=["系统镜像"])

@router.get("/list", response_model=List[dict])
def images_list(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-qingdao', description="区域 id"),
    service: ImageService = Depends(get_image_service)) -> List[dict]:
    items = service.list(provider_code, region_id)
    return Response.success(items)