from datetime import datetime

from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.bill_service import BillService

def get_bill_service(
   db: Session = Depends(get_cmp_db),
):
    return BillService(db)

router = APIRouter(prefix="/bill", tags=["费用"], dependencies=[Depends(require_user)])

# 查看用户账户信息
@router.get('/product_order_page_list')
def product_order_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    order: Optional[str] = Query(None, description="订单号"),
    instance_id: Optional[str] = Query(None, description="实例id"),
    start_at: Optional[datetime] = Query(None, description="订单的创建时间开始时间"),
    end_at: Optional[datetime] = Query(None, description="订单的创建时间结束时间"),
    service: BillService = Depends(get_bill_service)
):
    user_id = request.state.user.get('user_id')
    result = service.product_order_page_list(user_id, page, page_size, order, instance_id, start_at, end_at)
    return Response.success(result)

