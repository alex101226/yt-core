from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.invoice_service import InvoiceService
from app.schemas.cmp.invoice_schema import InvoiceSchema

def get_invoice_service(db: Session = Depends(get_cmp_db)):
    return InvoiceService(db)

router = APIRouter(
    prefix="/invoice",
    tags=["发票管理/发票抬头"],
    dependencies=[Depends(require_user)]
)

# 获取发票信息
@router.get('/invoice_info')
def invoice_info(
    request: Request,
    service: InvoiceService = Depends(get_invoice_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    result = service.invoice_info(parent_id)
    return Response.success(result)


# 设置发票抬头
@router.post('/invoice_setting')
def invoice_setting(
    request: Request,
    data: InvoiceSchema,
    service: InvoiceService = Depends(get_invoice_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.setting_invoice(request.state.user, data.model_dump())
    return Response.success(result)

