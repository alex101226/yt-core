from fastapi import APIRouter, Depends, Request, Query

from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.cloud_vendor_service import CloudVendorService
from app.schemas.cmp.cloud_vendor_schema import CloudVendorSchema, CloudVendorCreateSchema, CloudVendorUpdateSchema

def get_vendor_service(db: Session = Depends(get_cmp_db)):
    return CloudVendorService(db)

router = APIRouter(prefix="/cloud_vendor", tags=["云厂商"], dependencies=[Depends(require_user)])

# 创建云厂商
@router.post('/vendor_create')
def account_create(
    request: Request,
    data: CloudVendorCreateSchema,
    service: CloudVendorService = Depends(get_vendor_service)
):
    user_id = request.state.user.get('user_id')
    result = service.cloud_vendor_create(user_id, data.model_dump())
    return Response.success(result)

# 修改云厂商
@router.post('/vendor_update')
def account_update(
    data: CloudVendorUpdateSchema,
    service: CloudVendorService = Depends(get_vendor_service)
):
    result = service.cloud_vendor_update(data.model_dump())
    return Response.success(result)

# 分页云厂商
@router.get('/page_list')
def page_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    service: CloudVendorService = Depends(get_vendor_service)
):
    user_id = request.state.user.get('user_id')
    result = service.cloud_vendor_page_list(user_id, page, page_size)
    return Response.success(result)


