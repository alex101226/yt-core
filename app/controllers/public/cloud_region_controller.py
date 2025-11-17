from fastapi import APIRouter, Depends, Query
from app.schemas.public.cloud_region_schema import CloudRegionOut
from app.services.public.cloud_region_service import CloudRegionService
from app.services.public.dependencies import get_cloud_region_service
from app.common.response import Response

router = APIRouter(prefix="/cloud_regions", tags=["云区域配置"])

# 获取云区域
@router.get("/list", response_model=CloudRegionOut)
def list_regions(
    provider_code: str = Query(),
    service: CloudRegionService = Depends(get_cloud_region_service)
):
    items = service.sync_regions(provider_code)
    return Response.success(items)
