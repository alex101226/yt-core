from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db, get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user

from app.services.cmp.member_service import MemberService
from app.schemas.cmp.member_schema import MemberCreateSchema


def get_member_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db),
):
    return MemberService(sso_db, cmp_db)


router = APIRouter(prefix="/member", tags=["会员管理"], dependencies=[Depends(require_user)])


@router.post("/create")
def member_create(
    request: Request,
    data: MemberCreateSchema,
    service: MemberService = Depends(get_member_service),
):
    result = service.member_create(data, request.state.user)
    return Response.success(result)


@router.get("/page_list")
def member_page_list(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    member_name: str = Query(None, description="会员名称"),
    member_account: str = Query(None, description="会员账号"),
    member_type: str = Query(None, description="会员类型"),
    service: MemberService = Depends(get_member_service),
):
    result = service.member_page_list(page, page_size, member_name, member_account, member_type)
    return Response.success(result)


@router.get("/list")
def member_list(
    service: MemberService = Depends(get_member_service),
):
    result = service.member_list()
    return Response.success(result)


@router.get("/detail")
def member_detail(
    member_id: int = Query(..., description="会员ID"),
    service: MemberService = Depends(get_member_service),
):
    result = service.member_detail(member_id)
    return Response.success(result)


@router.delete("/delete")
def member_delete(
    member_id: int = Query(..., description="会员ID"),
    service: MemberService = Depends(get_member_service),
):
    result = service.member_delete(member_id)
    return Response.success(result)


@router.put("/toggle_freeze")
def member_toggle_freeze(
    member_id: int = Query(..., description="会员ID"),
    service: MemberService = Depends(get_member_service),
):
    result = service.member_toggle_freeze(member_id)
    return Response.success(result)
