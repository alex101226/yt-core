from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db, get_sso_db
from app.common.response import Response
from app.core.dependencies import require_user
from app.schemas.cmp.quota_schema import (
    QuotaApplyApproveSchema,
    QuotaApplyCreateSchema,
    QuotaApplyRejectSchema,
    QuotaCategoryToggleSchema,
)
from app.services.cmp.quota_service import QuotaService


def get_quota_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db),
):
    return QuotaService(sso_db, cmp_db)


router = APIRouter(prefix="/quota", tags=["配额管理"], dependencies=[Depends(require_user)])


@router.get("/category/list")
def category_list(service: QuotaService = Depends(get_quota_service)):
    return Response.success(service.category_list())


@router.put("/category/toggle")
def category_toggle(
    request: Request,
    data: QuotaCategoryToggleSchema,
    service: QuotaService = Depends(get_quota_service),
):
    return Response.success(service.category_toggle(request.state.user, data))


@router.post("/apply/create")
def apply_create(
    request: Request,
    data: QuotaApplyCreateSchema,
    service: QuotaService = Depends(get_quota_service),
):
    return Response.success(service.apply_create(request.state.user, data))


@router.get("/apply/page_list")
def apply_page_list(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    cloud_provider_code: str = Query(None, description="云厂商编码"),
    quantity_type: str = Query(None, description="数量类型"),
    enabled: bool = Query(None, description="是否启用"),
    approve_status: str = Query(None, description="审批状态"),
    service: QuotaService = Depends(get_quota_service),
):
    return Response.success(
        service.apply_page_list(page, page_size, cloud_provider_code, quantity_type, enabled, approve_status)
    )


@router.post("/apply/approve")
def apply_approve(
    request: Request,
    data: QuotaApplyApproveSchema,
    service: QuotaService = Depends(get_quota_service),
):
    return Response.success(service.apply_approve(request.state.user, data))


@router.post("/apply/reject")
def apply_reject(
    request: Request,
    data: QuotaApplyRejectSchema,
    service: QuotaService = Depends(get_quota_service),
):
    return Response.success(service.apply_reject(request.state.user, data))
