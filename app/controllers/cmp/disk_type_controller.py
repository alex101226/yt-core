from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, Query
from app.services.cmp.dependencies import get_disk_type_service
from app.services.cmp.disk_type_service import DiskTypeService
from app.common.response import Response

class InstanceChargeType(str, Enum):
    POSTPAID = "PostPaid"
    PREPAID = "PrePaid"
    SPOT = "Spot"

router = APIRouter(prefix="/disk_type", tags=["系统盘种类"])
@router.get("/list", response_model=List[dict])
def images_list(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-beijing', description="区域 id"),
    zone_id: str = Query('cn-beijing-g', description="可用区 id"),
    instance_type_id: str = Query('ecs.c2.medium', description="规格实例id"),
    instance_charge_type: InstanceChargeType = Query(InstanceChargeType.POSTPAID, description="计费方式"),
    service: DiskTypeService = Depends(get_disk_type_service)) -> List[dict]:
    items = service.disk_type_list(provider_code, region_id, zone_id, instance_type_id, instance_charge_type)
    return Response.success(items)