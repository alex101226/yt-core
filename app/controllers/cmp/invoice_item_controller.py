from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.constants.enums import InvoiceItemStatus

from app.services.cmp.invoice_item_service import InvoiceItemService

from app.schemas.cmp.invoice_schema import InvoiceRecordSchema


def get_invoice_service(db: Session = Depends(get_cmp_db)):
    return InvoiceItemService(db)

router = APIRouter(
    prefix="/invoice",
    tags=["发票管理/发票记录"],
    dependencies=[Depends(require_user)]
)

# 获取发票列表
@router.get('/invoice_page_list')
def invoice_info(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    # status: InvoiceItemStatus = Query(InvoiceItemStatus.ISSUED, description="发票状态：unissued / issued"),
    paid_start: Optional[str] = Query(None, description="支付起始时间，格式 YYYY-MM-DD"),
    paid_end: Optional[str] = Query(None, description="支付结束时间，格式 YYYY-MM-DD"),
    amount_min: Optional[float] = Query(None, description="最小实付金额"),
    amount_max: Optional[float] = Query(None, description="最大实付金额"),
    billing_period: Optional[str] = Query(None, description="账期，例如 2026-01"),
    service: InvoiceItemService = Depends(get_invoice_service)
):
    user_id = request.state.user.get('user_id')

    paid_start_dt = datetime.fromisoformat(paid_start) if paid_start else None
    paid_end_dt = datetime.fromisoformat(paid_end) if paid_end else None
    result = service.page_list(
        user_id, page, page_size, paid_start_dt, paid_end_dt, amount_min, amount_max, billing_period
    )
    return Response.success(result)

# 已开发票记录
@router.get('/invoice_record_page_list')
def invoice_item_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    status: str = Query(None, description="发票状态：unissued / issued"),
    apply_start: Optional[str] = Query(None, description="支付起始时间，格式 YYYY-MM-DD"),
    apply_end: Optional[str] = Query(None, description="支付结束时间，格式 YYYY-MM-DD"),
    invoice_no: Optional[str] = Query(None, description="发票号"),
    service: InvoiceItemService = Depends(get_invoice_service)
):
    user_id = request.state.user.get('user_id')
    apply_start_dt = datetime.fromisoformat(apply_start) if apply_start else None
    apply_end_dt = datetime.fromisoformat(apply_end) if apply_end else None
    result = service.page_list_record_issued(
        user_id,
        page, page_size, status, apply_start_dt, apply_end_dt, invoice_no
    )
    return Response.success(result)

# 欠票记录
@router.get('/invoice_overdue_page_list')
def invoice_overdue_list(
    request: Request,
    page: int = Query(..., description="第几页"),
    page_size: int = Query(..., description="页码"),
    service: InvoiceItemService = Depends(get_invoice_service)
):
    user_id = request.state.user.get('user_id')
    result = service.page_list_overdue(
        user_id=user_id,
        page=page,
        page_size=page_size,
    )
    return Response.success(result)

# 开具发票
@router.post('/issuing_invoices')
def invoice_setting(
    request: Request,
    data: InvoiceRecordSchema,
    service: InvoiceItemService = Depends(get_invoice_service)
):
    user_id = request.state.user.get('user_id')
    result = service.create_invoice_record(user_id, data)
    return Response.success(result)


@router.get('/invoice/statistics')
def invoice_statistics(
    request: Request,
    service: InvoiceItemService = Depends(get_invoice_service)
):
    user_id = request.state.user.get('user_id')
    result = service.get_invoice_statistics(user_id)
    return Response.success(result)

