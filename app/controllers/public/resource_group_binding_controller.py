from fastapi import APIRouter, Depends, Path, Query
from app.common.response import Response
from app.schemas.public.resource_group_binding_schema import (
    ResourceGroupBindingCreate,
    ResourceGroupBindingOut, ResourceGroupBindingPage
)
from app.services.public.resource_group_binding_service import ResourceGroupBindingService
from app.services.public.dependencies import get_resource_group_binding_service

router = APIRouter(prefix="/resource_group_bindings", tags=["资源组绑定"])


# 创建绑定
@router.post("/bind", response_model=ResourceGroupBindingOut)
def bind_resource(
    data: ResourceGroupBindingCreate,
    service: ResourceGroupBindingService = Depends(get_resource_group_binding_service),
):
    result = service.bind(data)
    return Response.success(result)


# 删除绑定
@router.delete("/{binding_id}")
def unbind_resource(
    binding_id: int = Path(..., description="绑定记录 ID"),
    service: ResourceGroupBindingService = Depends(get_resource_group_binding_service),
):
    service.unbind(binding_id)
    return Response.success()


# 获取某个组的资源绑定列表
@router.get("/group/{group_id}/page", response_model=ResourceGroupBindingPage)
def list_bindings_page(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ResourceGroupBindingService = Depends(get_resource_group_binding_service),
):
    total, items = service.list_bindings(group_id, page, page_size)
    return Response.success(
        ResourceGroupBindingPage(page=page, pageSize=page_size, total=total, items=items)
    )

