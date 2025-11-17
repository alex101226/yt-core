from fastapi import APIRouter, Query, Depends
from app.schemas.public.cloud_zone_schema import CloudZoneOut
from app.services.public.cloud_zone_service import CloudZoneService
from app.services.public.dependencies import get_cloud_zone_service
from app.common.response import Response

router = APIRouter(prefix="/cloud_zones", tags=["云可用区"])

# -------------------------------
# 分页查询
# -------------------------------
@router.get("/list", response_model=CloudZoneOut)
def list_zones(
    provider_code: str = Query('aliyun'),
    region_id: str = Query('cn-qingdao'),
    service: CloudZoneService = Depends(get_cloud_zone_service)
):
    items = service.sync_zones(provider_code, region_id)
    return Response.success(items)
