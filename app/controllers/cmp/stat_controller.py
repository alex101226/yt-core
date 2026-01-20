# app/controllers/stat_controller.py
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

from app.services.cmp.stat_service import StatService

router = APIRouter(prefix="/stat", tags=["资源信息统计"], dependencies=[Depends(require_user)])

# 资源信息
@router.get("/users/statistics")
def get_user_statistics(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')

    stats = service.get_user_statistics(user_id)
    return Response.success(stats)


# 金额支出统计
@router.get("/users/monthly-finance")
def get_monthly_finance(request: Request, db: Session = Depends(get_cmp_db)):
    service = StatService(db)

    user_id = request.state.user.get('user_id')

    stats = service.get_monthly_stats(user_id)
    return Response.success(stats)

# 账户概览---> 纵览
@router.get("/users/total_funds")
def get_total_funds(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    stats = service.get_total_funds(user_id)
    return Response.success(stats)

# 账户概览----> 当月总览
@router.get("/users/monthly_income")
def get_monthly_income(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    stats = service.get_monthly_total(user_id)
    return Response.success(stats)

# 传入年月，查可用额度，订单数量，消费金额，退款金额，可开票金额，已开票金额
@router.get("/users/monthly_pick_invoice")
def monthly_pick_invoice(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    stats = service.get_month_picker_total(user_id, date)
    return Response.success(stats)

# 费用总揽，图表
@router.get("/users/get_yearly_financial_chart")
def get_yearly_financial_chart(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    stats = service.get_yearly_financial_chart(user_id)
    return Response.success(stats)

# 查询成本总揽
@router.get("/users/get_monthly_top5_stats")
def get_monthly_top5_stats(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    result = service.get_monthly_top5_stats(user_id, date)
    return Response.success(result)

# 系统通知列表
@router.get("/user/message")
def get_user_statistics(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="页码"),
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)

    user_id = request.state.user.get('user_id')
    result = service.get_notifications_page_list(user_id, page, page_size)
    return Response.success(result)

# 获取未读通知数量
@router.get("/user/message/unread")
def get_user_statistics(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)

    user_id = request.state.user.get('user_id')
    result = service.get_unread_notification_count(user_id)
    return Response.success(result)

# 单条标记已读
@router.put("/user/message/read/{log_id}")
def mark_notification_read(
    request: Request,
    log_id: int,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)

    user_id = request.state.user.get('user_id')
    result = service.mark_notification_read(user_id, log_id)
    return Response.success(result)

# 一键已读
@router.post("/user/message/read/all")
def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)

    user_id = request.state.user.get('user_id')
    result = service.mark_all_notifications_read(user_id)
    return Response.success(result)
