from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.orm import Session

from app.core.dependencies import require_user

from app.common.response import Response
from app.core.logger import logger

from app.schemas.cmp.user_certificate_schema import (
    UserCertificateCreate, UserCertificateUpdate
)
from app.services.cmp.user_certificate_service import UserCertificateService

from app.common.dependencies import get_cmp_db

router = APIRouter(
    prefix="/user_certificates",
    tags=["用户云凭证"],
    dependencies=[Depends(require_user)]
)

def get_user_certificate_service(db: Session = Depends(get_cmp_db)):
    return UserCertificateService(db)

@router.post("/create")
def create_certificate(
    data: UserCertificateCreate,
    request: Request,
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    user = request.state.user
    payload = data.model_dump()
    payload['user_id'] = user.get('user_id')
    obj = service.create_certificate(payload)
    return Response.success(obj)

@router.get("/cer_list")
def certificates_list(
    request: Request,
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    user_id = request.state.user.get('user_id')
    items = service.certificate_list(user_id)
    return Response.success(items)


@router.get("/page_list")
def certificates_page_list(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    user_id = request.state.user.get('user_id')
    result = service.certificates_page_list(user_id, page, page_size)
    return Response.success(result)

@router.put("/update/{record_id}")
def update_certificate(
    record_id: int = Path(..., ge=1),
    data: UserCertificateUpdate = ...,
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    obj = service.update_certificate(record_id, **data.model_dump(exclude_unset=True))
    return Response.success(obj)

@router.delete("/delete/{record_id}")
def delete_certificate(
    record_id: int = Path(..., ge=1),
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    service.delete_certificate(record_id)
    return Response.success(message="删除成功")

@router.put("/set_default/{record_id}")
def set_default(
    certificate_id: int,
    request: Request,
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    user_id = request.state.user['user_id']
    obj = service.set_default_certificate(user_id, certificate_id)
    return Response.success(obj)

#   返回用户默认凭证信息
@router.get("/get_default_certificate")
def create_certificate(
    request: Request,
    service: UserCertificateService = Depends(get_user_certificate_service)
):
    user = request.state.user
    user_id = user.get('user_id')
    obj = service.get_default_certificate(user_id)

    return Response.success({
        "id": obj.id,
        "cloud_code": obj.cloud_code,
        "cloud_name": obj.cloud_name,
    })
