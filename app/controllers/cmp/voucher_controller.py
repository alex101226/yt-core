from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user

from app.services.cmp.voucher_service import VoucherService
from app.schemas.cmp.voucher_schema import VoucherTemplateCreateSchema, VoucherAssignCreateSchema


def get_voucher_service(db: Session = Depends(get_cmp_db)):
    return VoucherService(db)


router = APIRouter(prefix="/voucher", tags=["代金券"], dependencies=[Depends(require_user)])


@router.post("/template/create")
def template_create(
    request: Request,
    data: VoucherTemplateCreateSchema,
    service: VoucherService = Depends(get_voucher_service),
):
    result = service.template_create(data, request.state.user)
    return Response.success(result)


@router.get("/template/page_list")
def template_page_list(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    cloud_provider_code: str = Query(None, description="云厂商编码"),
    amount_min: float = Query(None, description="面值最小值"),
    amount_max: float = Query(None, description="面值最大值"),
    service: VoucherService = Depends(get_voucher_service),
):
    result = service.template_page_list(page, page_size, cloud_provider_code, amount_min, amount_max)
    return Response.success(result)


@router.delete("/template/delete")
def template_delete(
    template_id: int = Query(..., description="模板ID"),
    service: VoucherService = Depends(get_voucher_service),
):
    result = service.template_delete(template_id)
    return Response.success(result)


@router.post("/assign")
def assign(
    request: Request,
    data: VoucherAssignCreateSchema,
    service: VoucherService = Depends(get_voucher_service),
):
    result = service.assign(data, request.state.user)
    return Response.success(result)


@router.get("/assign/page_list")
def assign_page_list(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    service: VoucherService = Depends(get_voucher_service),
):
    result = service.assign_page_list(page, page_size)
    return Response.success(result)
