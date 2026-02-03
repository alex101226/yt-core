from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Request, Query

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.schemas.cmp.cloud_image import CloudImageCreate
from app.services.cmp.cloud_image_service import CloudImageService

def get_image_service(
   db: Session = Depends(get_cmp_db),
):
    return CloudImageService(db)

router = APIRouter(prefix="/cloud_image", tags=["自定义系统云镜像"], dependencies=[Depends(require_user)])

# 创建
@router.post("/create")
async def create_cloud_image(
    request: Request,
    data: CloudImageCreate,
    service: CloudImageService = Depends(get_image_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.create_image(request.state.user, data)
    return Response.success(result)



@router.get("/page_list")
def list_cloud_images(
    request: Request,
    page: int = Query(..., ge=1, description="页码，必传"),
    page_size: int = Query(..., ge=1, description="每页数量，必传"),
    cloud_provider_code: Optional[str] = Query(None, description="可选，云厂商代码"),
    region_id: Optional[str] = Query(None, description="可选，区域ID"),
    resource_group_id: Optional[str] = Query(None, description="可选，资源组ID"),
    image_name: Optional[str] = Query(None, description="可选，镜像名称"),
    service: CloudImageService = Depends(get_image_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    result = service.list_page_images(
        user_id=parent_id,
        page=page,
        page_size=page_size,
        cloud_provider_code=cloud_provider_code,
        region_id=region_id,
        resource_group_id=resource_group_id,
        image_name=image_name,
    )
    return Response.success(result)



