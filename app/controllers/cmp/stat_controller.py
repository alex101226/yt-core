# app/controllers/stat_controller.py
from fastapi import APIRouter, Depends, Request
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
