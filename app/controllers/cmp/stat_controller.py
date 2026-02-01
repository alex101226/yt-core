# app/controllers/stat_controller.py
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

from app.services.cmp.stat_service import StatService
# 实例管理：实例名称，资源组，云凭证，云厂商，区域，VPC，IP子网，计费方式（按量，包年月），网络类型：（私网，公网），实例类型（共享，独享），标签，描述，用户，状态，实例规格，宽带上限/网络计费类型，服务地址，，
# 证书管理：证书名称，资源组，云厂商，云证书，区域，证书内容，证书密钥，标签，备注，状态，证书域名，关联扩展域名，过期时间，关联监听，用户
# 访问控制：策略名称，资源组，云厂商，云凭证，区域，批量添加地址，备注，状态，源地址，关联监听，用户，
router = APIRouter(prefix="/stat", tags=["资源信息统计"], dependencies=[Depends(require_user)])

# 资源信息
@router.get("/users/statistics")
def get_user_statistics(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')

    stats = service.get_user_statistics(parent_id)
    return Response.success(stats)


# 金额支出统计
@router.get("/users/monthly-finance")
def get_monthly_finance(request: Request, db: Session = Depends(get_cmp_db)):
    service = StatService(db)

    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')

    stats = service.get_monthly_stats(parent_id)
    return Response.success(stats)

# 账户概览---> 纵览
@router.get("/users/total_funds")
def get_total_funds(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    stats = service.get_total_funds(parent_id)
    return Response.success(stats)

# 账户概览----> 当月总览
@router.get("/users/monthly_income")
def get_monthly_income(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    stats = service.get_monthly_total(parent_id)
    return Response.success(stats)

# 传入年月，查可用额度，订单数量，消费金额，退款金额，可开票金额，已开票金额
@router.get("/users/monthly_pick_invoice")
def monthly_pick_invoice(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    stats = service.get_month_picker_total(parent_id, date)
    return Response.success(stats)

# 费用总揽，图表
@router.get("/users/get_yearly_financial_chart")
def get_yearly_financial_chart(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    stats = service.get_yearly_financial_chart(parent_id)
    return Response.success(stats)

# 查询成本总揽
@router.get("/users/get_monthly_top5_stats")
def get_monthly_top5_stats(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.get_monthly_top5_stats(parent_id, date)
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

    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.get_notifications_page_list(parent_id, page, page_size)
    return Response.success(result)

# 获取未读通知数量
@router.get("/user/message/unread")
def get_user_statistics(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)

    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    result = service.get_unread_notification_count(parent_id)
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
