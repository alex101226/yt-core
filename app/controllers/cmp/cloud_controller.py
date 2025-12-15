from typing import Optional

from fastapi import APIRouter, Depends, Query
from enum import Enum
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.services.cloud.aliyun.aliyun_service import AliyunService
from app.common.filter_spec import filter_spec, filter_available_instances, fetch_prices_concurrent
from app.core.logger import logger

from app.services.cmp.user_certificate_service import UserCertificateService

def get_user_certificate_service(db: Session = Depends(get_cmp_db)):
    return UserCertificateService(db)

router = APIRouter(prefix="/cloud", tags=["云厂商信息"])

# -----------------------------
# Example: List Regions
# -----------------------------
@router.get("/regions")
async def list_regions(
    user_id: int = Query(..., description="用户id"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)

    aliyun_service = AliyunService(access_key_id=cer_data.cloud_access_key_id, access_key_secret=cer_data.cloud_access_key_secret)
    regions = await aliyun_service.list_regions()
    return Response.success(regions)

# -----------------------------
# List Zones
# -----------------------------
@router.get("/zones")
async def list_zones(
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )

    zones = await aliyun_service.list_zones(region_id)
    return Response.success(zones)

# -----------------------------
# List Images
# -----------------------------
@router.get("/images")
async def list_images(
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    instance_type_id: str = Query(..., description="Instance Type ID"),
    architecture: str = Query(..., description="Architecture, e.g., x86_64"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )
    images = await aliyun_service.list_images(region_id, instance_type_id, architecture)
    return Response.success(images)

# -----------------------------
# List 系统盘
# -----------------------------
class InstanceChargeType(str, Enum):
    POSTPAID = "PostPaid"
    PREPAID = "PrePaid"
    SPOT = "Spot"

@router.get("/system_disk_categories")
async def list_system_disk_categories(
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    zone_id: str = Query(..., description="Zone ID"),
    instance_type_id: str = Query(..., description="Instance Type ID"),
    instance_charge_type: str = Query(..., description="计费方式"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )
    categories = await aliyun_service.list_system_disk_categories(region_id, zone_id, instance_type_id, instance_charge_type)
    return Response.success(categories)

# -----------------------------
# List Instance Types
# -----------------------------
# @router.get("/instance_types")
# async def list_instance_types(
#     user_id: int = Query(7, description="用户id"),
#     region_id: str = Query('cn-beijing', description="Region ID"),
#     service: UserCertificateService = Depends(get_user_certificate_service)
# ):
#     # 1️⃣ 查用户凭证
#     cer_data = service.get_user_ak(user_id)
#     aliyun_service = AliyunService(
#         access_key_id=cer_data.cloud_access_key_id,
#         access_key_secret=cer_data.cloud_access_key_secret
#     )
#     types = await aliyun_service.list_instance_types(region_id)
#     return Response.success(types)

# -----------------------------
# List Available Instance Types
# -----------------------------
@router.get("/spec_page_list")
async def list_available_instance_types(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="页码"),
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    zone_id: str = Query(..., description="Zone ID"),
    instance_charge_type: str = Query(..., description="计费方式"),
    disk_category: str = Query(..., description="系统盘种类，默认 cloud_essd"),
    cpu_number: Optional[int] = Query(None, description="cpu核数"),
    memory_number: Optional[int] = Query(None, description="内存大小"),
    gpu_name: Optional[str] = Query(None, description="GPU规格名称 "),
    instance_spec: Optional[str] = Query(None, description="实例规格名称"),
    hide_soldout: Optional[bool] = Query(None, description="隐藏售罄的规格"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )
    types = await aliyun_service.list_instance_types(region_id)
    # logger.info(f"types: {types}")
    available_raw = await aliyun_service.list_available_instance_types(region_id, zone_id, instance_charge_type, disk_category)

    available_map = {}
    for item in available_raw:
        it_id = item.get("instance_type_id")
        # 标准化状态字段名
        status = item.get("status_category") or item.get("status") or item.get("status")
        available_map[it_id] = {"status_category": status}

    if not available_map:
        return {"total": 0, "page": page, "page_size": page_size, "items": []}
    # 3) 批量从 DB 里拿这些 instanceType 的详细信息（一次 SQL）
    all_ids = list(available_map.keys())
    db_map = await filter_spec(all_ids, types)

    # logger.info(f'available_map: {available_map}')
    # 4) 在内存中过滤（CPU / 内存 / GPU 等）
    filtered = filter_available_instances(
        available_map=available_map,
        db_map=db_map,
        cpu_number=cpu_number,
        memory_number=memory_number,
        gpu_name=gpu_name,
        instance_spec=instance_spec,
        hide_soldout=bool(hide_soldout),
    )
    # logger.info(f"filtered: {filtered}")
    # 5) 分页（注意：分页在过滤之后）
    page = max(1, int(page or 1))
    page_size = max(1, int(page_size or 10))
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = filtered[start:end]

    if not page_items:
        return {"total": total, "page": page, "page_size": page_size, "items": []}

    # 6) 并发查询价格（只查当前页的 items，避免 N 次全量调用）
    instance_type_ids_page = [it["instance_type_id"] for it in page_items]

    prices = fetch_prices_concurrent(
        client=aliyun_service,
        region_id=region_id,
        instance_type_ids=instance_type_ids_page,
        instance_charge_type=instance_charge_type,
        system_disk_category=disk_category,
        max_workers=10,
    )

    # 7) 合并并返回（把价格合并到每个 item）
    out_items = []
    for it in page_items:
        it_id = it["instance_type_id"]
        out_items.append({
            "instance_type_id": it_id,
            "cpu_core_count": it["cpu_core_count"],
            "memory_size": it["memory_size"],
            "gpu_amount": it["gpu_amount"],
            "gpu_spec": it["gpu_spec"],
            "gpu_memory": it["gpu_memory"],
            "architecture": it["architecture"],
            "zone_id": zone_id,
            "price": prices.get(it_id, 0),
            "status_category": it.get("status_category"),
        })

    obj = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": out_items,
    }
    return Response.success(obj)

# -----------------------------
# Instance Price
# -----------------------------
@router.get("/cloud_price")
async def instance_price(
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    instance_type_id: str = Query(..., description="Instance Type ID"),
    disk_category: str = Query(..., description="系统盘种类，默认 cloud_essd"),
    system_disk_size: int = Query(..., description="系统盘大小"),
    instance_charge_type: str = Query(..., description="计费方式"),
    period: Optional[int] = Query(None, description="包年包月要传递的参数"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )
    price = await aliyun_service.cloud_price(
        region_id, instance_type_id, disk_category, system_disk_size,
        instance_charge_type, period
    )
    return Response.success(price)


# 获取eip价格
class InternetChargeType(str, Enum):
    PayByTraffic = "PayByTraffic"
    PayByBandwidth = "PayByBandwidth"

@router.get("/eip_price")
def instance_price(
    user_id: int = Query(..., description="用户id"),
    region_id: str = Query(..., description="Region ID"),
    bandwidth: int = Query(..., description="系统盘大小"),
    internet_charge_type: str = Query(..., description="计费方式"),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    # 1️⃣ 查用户凭证
    cer_data = service.get_user_ak(user_id)
    aliyun_service = AliyunService(
        access_key_id=cer_data.cloud_access_key_id,
        access_key_secret=cer_data.cloud_access_key_secret
    )
    price = aliyun_service.eip_price(region_id, bandwidth, internet_charge_type)
    return Response.success(price)