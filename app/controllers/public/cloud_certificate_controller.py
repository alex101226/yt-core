from fastapi import APIRouter, Depends, Path, Query
from app.common.response import Response
from app.schemas.public.cloud_certificate_schema import (
    CloudCertificateCreate, CloudCertificateUpdate, CloudCertificateOut, CloudCertificatePage
)
from app.services.public.dependencies import get_cloud_certificate_service
from app.services.public.cloud_certificate_service import CloudCertificateService

router = APIRouter(prefix="/cloud_certificates", tags=["云凭证"])

@router.post("/create", response_model=CloudCertificateOut)
def create_certificate(data: CloudCertificateCreate, service: CloudCertificateService = Depends(get_cloud_certificate_service)):
    obj = service.create_certificate(**data.model_dump())
    return Response.success(obj)

@router.get("/pageList", response_model=CloudCertificatePage)
def list_certificates(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
                      service: CloudCertificateService = Depends(get_cloud_certificate_service)):
    total, items = service.list_certificates(page, page_size)
    return Response.success(CloudCertificatePage(page=page, pageSize=page_size, total=total, items=items))

@router.put("/update/{record_id}", response_model=CloudCertificateOut)
def update_certificate(record_id: int = Path(..., ge=1), data: CloudCertificateUpdate = ...,
                       service: CloudCertificateService = Depends(get_cloud_certificate_service)):
    obj = service.update_certificate(record_id, **data.model_dump(exclude_unset=True))
    return Response.success(obj)

@router.delete("/delete/{record_id}")
def delete_certificate(record_id: int = Path(..., ge=1), service: CloudCertificateService = Depends(get_cloud_certificate_service)):
    service.delete_certificate(record_id)
    return Response.success(message="删除成功")
