from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db, get_sso_db
from app.common.response import Response
from app.core.dependencies import require_user
from app.services.cmp.studio_service import StudioService


def get_studio_service(
    sso_db: Session = Depends(get_sso_db),
    cmp_db: Session = Depends(get_cmp_db),
):
    return StudioService(sso_db, cmp_db)


router = APIRouter(prefix="/studio", tags=["Studio"], dependencies=[Depends(require_user)])


@router.get("/page_list")
def studio_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    studio_name: Optional[str] = Query(None, description="Studio名称"),
    service: StudioService = Depends(get_studio_service),
):
    return Response.success(service.page_list(request.state.user, page, page_size, studio_name))


@router.get("/list")
def studio_list(
    request: Request,
    service: StudioService = Depends(get_studio_service),
):
    return Response.success(service.studio_list(request.state.user))


@router.get("/overview")
def studio_overview(
    request: Request,
    studio_id: Optional[int] = Query(None, description="Studio ID"),
    service: StudioService = Depends(get_studio_service),
):
    return Response.success(service.overview(request.state.user, studio_id))


@router.get("/node/page_list")
def studio_node_page_list(
    request: Request,
    studio_id: Optional[int] = Query(None, description="Studio ID"),
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页条数"),
    node_name: Optional[str] = Query(None, description="节点名称"),
    service: StudioService = Depends(get_studio_service),
):
    return Response.success(service.node_page_list(request.state.user, studio_id, page, page_size, node_name))
