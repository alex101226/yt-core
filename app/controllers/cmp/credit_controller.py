from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db, get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user

from app.services.cmp.credit_service import CreditService
from app.schemas.cmp.credit_schema import CreditGrantCreateSchema, CreditApproveSchema, CreditRejectSchema


def get_credit_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db),
):
    return CreditService(sso_db, cmp_db)


router = APIRouter(prefix="/credit", tags=["低佣金"], dependencies=[Depends(require_user)])


@router.post("/grant")
def credit_grant(
    request: Request,
    data: CreditGrantCreateSchema,
    service: CreditService = Depends(get_credit_service),
):
    result = service.grant(data, request.state.user)
    return Response.success(result)


@router.post("/approve")
def credit_approve(
    request: Request,
    data: CreditApproveSchema,
    service: CreditService = Depends(get_credit_service),
):
    result = service.approve(data.grant_id, request.state.user)
    return Response.success(result)


@router.post("/reject")
def credit_reject(
    request: Request,
    data: CreditRejectSchema,
    service: CreditService = Depends(get_credit_service),
):
    result = service.reject(data.grant_id, data.reason, request.state.user)
    return Response.success(result)


@router.get("/balance")
def credit_balance(
    request: Request,
    member_id: int = Query(None, description="会员ID(内部人员可查他人)"),
    service: CreditService = Depends(get_credit_service),
):
    result = service.balance(request.state.user, member_id)
    return Response.success(result)


@router.get("/overview")
def credit_overview(
    request: Request,
    service: CreditService = Depends(get_credit_service),
):
    result = service.overview(request.state.user)
    return Response.success(result)


@router.get("/grant/page_list")
def credit_grant_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    member_id: int = Query(None, description="会员ID"),
    cloud_provider_code: str = Query(None, description="云厂商编码"),
    status: str = Query(None, description="状态"),
    approve_status: str = Query(None, description="审批状态"),
    service: CreditService = Depends(get_credit_service),
):
    result = service.grant_page_list(
        request.state.user, page, page_size, member_id, cloud_provider_code, status, approve_status
    )
    return Response.success(result)


@router.get("/flow/page_list")
def credit_flow_page_list(
    request: Request,
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    member_id: int = Query(None, description="会员ID(内部人员可查他人)"),
    service: CreditService = Depends(get_credit_service),
):
    result = service.flow_page_list(request.state.user, page, page_size, member_id)
    return Response.success(result)
