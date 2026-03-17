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
    stats = service.get_user_statistics(request.state.user)
    return Response.success(stats)


# 金额支出统计
@router.get("/users/monthly-finance")
def get_monthly_finance(request: Request, db: Session = Depends(get_cmp_db)):
    service = StatService(db)
    stats = service.get_monthly_stats(request.state.user)
    return Response.success(stats)

# 账户概览---> 纵览
@router.get("/users/total_funds")
def get_total_funds(
    request: Request,
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    stats = service.get_total_funds(request.state.user)
    return Response.success(stats)

# 账户概览----> 当月总览
@router.get("/users/monthly_income")
def get_monthly_income(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    stats = service.get_monthly_total(request.state.user)
    return Response.success(stats)

# 传入年月，查可用额度，订单数量，消费金额，退款金额，可开票金额，已开票金额
@router.get("/users/monthly_pick_invoice")
def monthly_pick_invoice(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    stats = service.get_month_picker_total(request.state.user, date)
    return Response.success(stats)

# 费用总揽，图表
@router.get("/users/get_yearly_financial_chart")
def get_yearly_financial_chart(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    stats = service.get_yearly_financial_chart(request.state.user)
    return Response.success(stats)

# 查询成本总揽
@router.get("/users/get_monthly_top5_stats")
def get_monthly_top5_stats(
    request: Request,
    date: str,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    result = service.get_monthly_top5_stats(request.state.user, date)
    return Response.success(result)

# 纳管机器统计
@router.get("/cps/cloud/count")
def get_cps_count(
    request: Request,
    db: Session = Depends(get_cmp_db)

):
    service = StatService(db)
    result = service.cps_state_server_count(request.state.user)
    return Response.success(result)

# 纳管，gpu分配率统计   gpu_rate_trend
@router.get("/cps/gpu_rate")
def get_cps_gpu_rate(
    request: Request,
    time: str = '1h',
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    result = service.gpu_rate_trend(request.state.user, time)
    return Response.success(result)

# 系统通知列表
@router.get("/user/message")
def get_user_statistics(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="页码"),
    system: int = Query(1, description="系统类型"),
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    result = service.get_notifications_page_list(user_id, page, page_size, system)
    return Response.success(result)

# 获取未读通知数量
@router.get("/user/message/unread")
def get_user_statistics(
    request: Request,
    system: int = Query(1, description="系统类型"),
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    user_id = request.state.user.get('user_id')
    result = service.get_unread_notification_count(user_id, system)
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

# 总收入趋势
@router.get("/users/total_income_trend")
def get_total_income_trend(
    request: Request,
    start_at: str = Query(None, description="开始时间，ISO8601"),
    end_at: str = Query(None, description="结束时间，ISO8601"),
    db: Session = Depends(get_cmp_db)
):
    service = StatService(db)
    result = service.get_total_income_trend(request.state.user, start_at, end_at)
    return Response.success(result)


# 运营概览
@router.get("/operation/overview")
def get_operation_overview(
    request: Request,
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    result = service.get_operation_overview(request.state.user)
    return Response.success(result)


# 运营排行榜/分布统计
@router.get("/operation/rankings")
def get_operation_rankings(
    request: Request,
    start_at: str = Query(None, description="开始时间，ISO8601"),
    end_at: str = Query(None, description="结束时间，ISO8601"),
    cloud_provider_code: str = Query(None, description="云厂商编码"),
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    result = service.get_operation_rankings(request.state.user, start_at, end_at, cloud_provider_code)
    return Response.success(result)


@router.get("/operation/resource_consume/options")
def get_resource_consume_options(
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    result = service.get_resource_consume_options()
    return Response.success(result)


@router.get("/operation/resource_consume/page_list")
def get_resource_consume_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    cloud_provider_code: str = Query(None, description="云厂商编码"),
    region_id: str = Query(None, description="区域ID"),
    instance_keyword: str = Query(None, description="实例ID或实例名称关键字"),
    product_name: str = Query(None, description="产品名称"),
    consume_type: str = Query(None, description="消费类型"),
    member_id: int = Query(None, description="会员ID"),
    db: Session = Depends(get_cmp_db),
):
    service = StatService(db)
    result = service.get_resource_consume_page_list(
        current_user=request.state.user,
        page=page,
        page_size=page_size,
        cloud_provider_code=cloud_provider_code,
        region_id=region_id,
        instance_keyword=instance_keyword,
        product_name=product_name,
        consume_type=consume_type,
        member_id=member_id,
    )
    return Response.success(result)
