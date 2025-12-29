from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.schemas.cmp.invoice_email_schema import InvoiceEmailSchema, InvoiceEmailUpdate
from app.services.cmp.invoice_email_service import InvoiceEmailService

def get_invoice_email_service(
   db: Session = Depends(get_cmp_db),
):
    return InvoiceEmailService(db)

router = APIRouter(
    prefix="/invoice_email",
    tags=["发票管理/邮件地址"],
    dependencies=[Depends(require_user)]
)

# 分页
@router.get('/invoice_email_page_list')
def invoice_email_page_list(
    request: Request,
    page: int,
    page_size: int,
    service: InvoiceEmailService = Depends(get_invoice_email_service)
):
    user_id = request.state.user.get('user_id')
    result = service.invoice_email_page_list(user_id, page, page_size)
    return Response.success(result)

@router.post('/invoice_email_create')
def invoice_email_create(
    request: Request,
    data: InvoiceEmailSchema,
    service: InvoiceEmailService = Depends(get_invoice_email_service)
):
    user_id = request.state.user.get('user_id')
    result = service.invoice_email_create(user_id, data.model_dump())
    return Response.success(result)

# 修改
@router.post('/invoice_email_update')
def invoice_email_update(
    data: InvoiceEmailUpdate,
    service: InvoiceEmailService = Depends(get_invoice_email_service),
):
    result = service.invoice_email_update(data.model_dump())
    return Response.success(result)

# 删除
@router.delete('/invoice_email_delete')
def invoice_email_delete(
    email_id: int,
    service: InvoiceEmailService = Depends(get_invoice_email_service),
):
    result = service.invoice_email_delete(email_id)
    return Response.success(result)

# 设置默认邮件
@router.put('/invoice_email_default')
def invoice_email_default(
    request: Request,
    email_id: int,
    service: InvoiceEmailService = Depends(get_invoice_email_service),
):
    user_id = request.state.user.get('user_id')
    result = service.invoice_email_default(user_id, email_id)
    return Response.success(result)
