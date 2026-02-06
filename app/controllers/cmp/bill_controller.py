from datetime import datetime

from fastapi import APIRouter, Depends, Request, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.services.cmp.order_service import OrderService

from app.services.cmp.bill_service import BillService

def get_order_service(db: Session = Depends(get_cmp_db)):
    return OrderService(db)

def get_bill_service(
   db: Session = Depends(get_cmp_db),
):
    return BillService(db)

router = APIRouter(prefix="/bill", tags=["费用"], dependencies=[Depends(require_user)])

# 商品订单
@router.get('/product_order_page_list')
def product_order_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    order: Optional[str] = Query(None, description="订单号"),
    instance_id: Optional[str] = Query(None, description="实例id"),
    start_at: Optional[datetime] = Query(None, description="订单的创建时间开始时间"),
    end_at: Optional[datetime] = Query(None, description="订单的创建时间结束时间"),
    service: OrderService = Depends(get_order_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.product_order_page_list(parent_id, page, page_size, order, instance_id, start_at, end_at)
    return Response.success(result)


# 订单明细
@router.get('/order_detail_page_list')
def order_detail_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    instance_id: Optional[str] = Query(None, description="每页条数"),
    consume_type: Optional[str] = Query(None, description="消费类型"),
    provider_code: Optional[str] = Query(None, description="云厂商"),
    billing_period: Optional[str] = Query(None, description="账期"),
    service: OrderService = Depends(get_order_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.order_detail_page_list(
        parent_id, page, page_size, instance_id, consume_type, provider_code, billing_period
    )
    return Response.success(result)


# 账单明细
@router.get('/bill_order_page_list')
def bill_order_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    billing_id: Optional[str] = Query(None, description="账单id"),
    start_month: str = Query(..., description="开始月份"),
    end_month: str = Query(..., description="结束月份"),
    consume_type: Optional[str] = Query(None, description="消费类型"),
    billing_type: Optional[str] = Query(None, description="账单类型"),
    provider_code: Optional[str] = Query(None, description="云厂商"),
    billing_status: Optional[str] = Query(None, description="账单状态"),
    service: BillService = Depends(get_bill_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.billing_flows_page_list(
        parent_id, page, page_size, billing_id, start_month, end_month, consume_type, billing_type,
        provider_code, billing_status
    )
    return Response.success(result)


# 收支明细
@router.get('/billing_flow_detail_page_list')
def billing_flow_detail_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    flow_no: Optional[str] = Query(None, description="交易号"),
    third_trade_no: Optional[str] = Query(None, description="流水号"),
    direction: Optional[str] = Query(None, description="收支类型"),
    flow_type: Optional[str] = Query(None, description="交易类型"),
    channel: Optional[str] = Query(None, description="交易渠道"),
    # fund_type: Optional[str] = Query(None, description="资金形式"),
    service: BillService = Depends(get_bill_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.billing_flow_detail_page_list(
        parent_id, page, page_size, flow_no, third_trade_no, direction, flow_type,
        channel
    )
    return Response.success(result)


# 月汇总
@router.get('/monthly_fund_summary_page_list')
def monthly_fund_summary_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    start_month: str = Query(..., description="开始月份"),
    end_month: str = Query(..., description="结束月份"),
    direction: Optional[str] = Query(None, description="收支类型"),
    flow_type: Optional[str] = Query(None, description="交易类型"),
    channel: Optional[str] = Query(None, description="交易渠道"),
    flow_no: Optional[str] = Query(None, description="流水号"),
    # third_trade_no: Optional[str] = Query(None, description="交易单号"),
    service: BillService = Depends(get_bill_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.monthly_fund_summary(
        parent_id, page, page_size, start_month, end_month, direction, flow_type,
        channel, flow_no
    )
    return Response.success(result)


@router.get("/unsubscribe_page_list")
def unsubscribe_page_list(
    request: Request,
    page: int = Query(1, description="分页"),
    page_size: int = Query(10, description="每页条数"),
    service: BillService = Depends(get_bill_service)
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')

    result = service.unsubscribe_page_list(parent_id, page, page_size)
    return Response.success(result)

@router.put('/unsubscribe/{task_id}')
def unsubscribe(
    task_id: int,
    service: BillService = Depends(get_bill_service)
):
    result = service.set_unsubscribe(task_id)
    return Response.success(result)


