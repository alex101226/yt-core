from typing import Optional

from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

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
    user_id = request.state.user.get('user_id')
    result = service.create_image(user_id, data)
    return Response.success(result)
