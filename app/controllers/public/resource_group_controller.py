from fastapi import APIRouter, Depends, Path, Query
from app.schemas.public.resource_group_schema import (
    ResourceGroupCreate, ResourceGroupUpdate, ResourceGroupOut, ResourceGroupPage
)
from app.services.public.resource_group_service import ResourceGroupService
from app.services.public.dependencies import get_resource_group_service
from app.common.response import Response

router = APIRouter(prefix="/resource_groups", tags=["资源组管理"])

# 创建资源组
@router.post("/create", response_model=ResourceGroupOut)
def create_group(
    data: ResourceGroupCreate,
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    group = service.create_group(data.model_dump())
    return Response.success(group, "创建成功")

# 修改资源组
@router.put("/update/{record_id}", response_model=ResourceGroupOut)
def update_group(
    record_id: int = Path(..., ge=1, description="记录ID"),
    data: ResourceGroupUpdate = ...,
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    group = service.update_group(record_id, data.model_dump(exclude_unset=True))
    return Response.success(group, "修改成功")

# 删除资源组
@router.delete("/delete/{record_id}")
def delete_group(
    record_id: int = Path(..., ge=1, description="记录ID"),
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    service.delete_group(record_id)
    return Response.success(message="删除成功")

# 分页查询资源组
@router.get("/page_list", response_model=ResourceGroupPage)
def list_groups(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    total, items = service.list_groups(page, page_size)
    return Response.success(ResourceGroupPage(page=page, pageSize=page_size, total=total, items=items))
