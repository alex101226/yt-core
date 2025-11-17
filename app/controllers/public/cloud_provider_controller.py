# app/controllers/public/cloud_provider_controller.py

from fastapi import APIRouter, Depends, Path, Query

from app.schemas.public.cloud_provider_schema import (
    CloudProviderCreate,
    CloudProviderUpdate,
    CloudProviderOut,
    CloudProviderPage
)

from app.services.public.cloud_provider_service import CloudProviderService
from app.services.public.dependencies import get_cloud_provider_service
from app.common.response import Response

router = APIRouter(prefix="/cloud_providers", tags=["云厂商配置"])

# 创建云厂商
@router.post("/create", response_model=CloudProviderOut)
def create_provider(
    data: CloudProviderCreate,
    service: CloudProviderService = Depends(get_cloud_provider_service)
):
    provider = service.create_provider(**data.model_dump())
    return Response.success(provider)


# 更新云厂商
@router.put("/update/{record_id}", response_model=CloudProviderOut)
def update_provider(
    record_id: int = Path(..., ge=1),
    data: CloudProviderUpdate = ...,
    service: CloudProviderService = Depends(get_cloud_provider_service)
):
    provider = service.update_provider(record_id, **data.model_dump(exclude_unset=True))
    return Response.success(provider)


# 删除云厂商
@router.delete("/delete/{record_id}")
def delete_provider(
    record_id: int = Path(..., ge=1),
    service: CloudProviderService = Depends(get_cloud_provider_service)
):
    service.delete_provider(record_id)
    return Response.success(message="删除成功")


# 分页
@router.get("/page_list", response_model=CloudProviderPage)
def list_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: CloudProviderService = Depends(get_cloud_provider_service)
):
    total, items = service.list_providers(page, page_size)
    page_data = CloudProviderPage(page=page, pageSize=page_size, total=total, items=items)
    return Response.success(page_data)
