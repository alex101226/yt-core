from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.services.cmp.dict_service import DictService

from app.schemas.cmp.dict_schema import DictItemCreate, DictItemUpdate, DictItemOut, DictItemListOut

from app.enums.enums import DictType


# 云厂商，区域，可用区 云凭证，VPC，IP子网，安全组，计费方式，购买数量，规格列表，镜像及磁盘（要安装GPU驱动嘛，要查驱动？）
def get_dict_service(
   db: Session = Depends(get_cmp_db),
):
    return DictService(db)


router = APIRouter(prefix="/dict", tags=["字典"])

# -------------------------
# 查询某个 type_code 下的字典列表
# -------------------------
@router.get("/list", response_model=List[DictItemOut])
def get_dict_by_type(
        type_code: str = Query(..., description="字典类型"),
        service: DictService = Depends(get_dict_service)
):
    items = service.list_by_type(type_code)
    return Response.success(items)


# -------------------------
# 分页查询字典项
# -------------------------
# @router.get("/page_list", response_model=DictItemListOut)
# def list_dict_items(
#     type_code: Optional[str] = Query(None, description="字典类型"),
#     keyword: Optional[str] = Query(None, description="模糊查询关键字"),
#     page: int = Query(1, ge=1),
#     size: int = Query(10, ge=1),
#     service: DictService = Depends(get_dict_service)
# ):
#     items = service.list(type_code=type_code, keyword=keyword, page=page, size=size)
#     return Response.success(items)


# -------------------------
# 创建字典项
# -------------------------
# @router.post("/create", response_model=DictItemOut)
# def create_dict_item(item_in: DictItemCreate, service: DictService = Depends(get_dict_service)):
#     result = service.create(item_in)
#     return Response.success(result)


# -------------------------
# 更新字典项
# -------------------------
# @router.put("/update/{type_code}/{item_code}", response_model=DictItemOut)
# def update_dict_item(type_code: str, item_code: str, item_in: DictItemUpdate, service: DictService = Depends(get_dict_service)):
#     updated = service.update(type_code, item_code, item_in)
#     return Response.success(updated)


# -------------------------
# 删除字典项
# -------------------------
# @router.delete("/delete/{dict_id}", response_model=dict)
# def delete_dict_item(dict_id: int, service: DictService = Depends(get_dict_service)):
#     service.delete(dict_id)
#     return Response.success(message="删除成功")
