from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.schemas.cmp.resource_group_schema import (
    ResourceGroupCreate, ResourceGroupUpdate, ResourceGroupOut,
    ResourceGroupPage, ResourceGroupBindingOut, ResourceGroupBindingCreate, ResourceGroupBindingPage
)
from app.services.cmp.resource_group_service import ResourceGroupService
from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user


def get_resource_group_service(db: Session = Depends(get_cmp_db)):
    return ResourceGroupService(db)


router = APIRouter(
    prefix="/resource_groups",
    tags=["资源组管理"],
    dependencies=[Depends(require_user)]
)

# 创建资源组
@router.post("/group_create", response_model=ResourceGroupOut)
def create_group(
    data: ResourceGroupCreate,
    request: Request,
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    user_id = request.state.user.get('user_id')
    payload = data.model_dump()
    payload['user_id'] = user_id
    group = service.create_group(payload)
    return Response.success(group)

# 修改资源组
# @router.put("/update/{record_id}", response_model=ResourceGroupOut)
# def update_group(
#     record_id: int = Path(..., ge=1, description="记录ID"),
#     data: ResourceGroupUpdate = ...,
#     service: ResourceGroupService = Depends(get_resource_group_service)
# ):
#     group = service.update_group(record_id, data.model_dump())
#     return Response.success(group)

# 删除资源组
# @router.delete("/delete/{record_id}")
# def delete_group(
#     record_id: int = Path(..., ge=1, description="记录ID"),
#     service: ResourceGroupService = Depends(get_resource_group_service)
# ):
#     service.delete_group(record_id)
#     return Response.success(message="删除成功")

# 分页查询资源组
@router.get("/group_page_list", response_model=ResourceGroupPage)
def list_groups(
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数"),
    service: ResourceGroupService = Depends(get_resource_group_service)
):
    total, items = service.list_groups(page, page_size)
    return Response.success(ResourceGroupPage(page=page, pageSize=page_size, total=total, items=items))



# 创建绑定
# @router.post("/resource_bind", response_model=ResourceGroupBindingOut)
# def bind_resource(
#     data: ResourceGroupBindingCreate,
#     service: ResourceGroupService = Depends(get_resource_group_service),
# ):
#     result = service.bind(data)
#     return Response.success(result)


# 删除绑定
@router.delete("/{binding_id}")
def unbind_resource(
    binding_id: int = Path(..., description="绑定记录 ID"),
    service: ResourceGroupService = Depends(get_resource_group_service),
):
    result = service.unbind(binding_id)
    return Response.success(result)


# 获取某个组的资源绑定列表
@router.get("/resource_page_list/{group_id}", response_model=ResourceGroupBindingPage)
def list_bindings_page(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: ResourceGroupService = Depends(get_resource_group_service),
):
    total, items = service.list_bindings(group_id, page, page_size)
    return Response.success(
        ResourceGroupBindingPage(page=page, pageSize=page_size, total=total, items=items)
    )
