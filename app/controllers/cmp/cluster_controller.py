from typing import Optional, List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user
from app.common.response import Response

from app.services.cmp.cluster_service import ClusterService
from app.schemas.cmp.cluster_schema import ClusterCreateSchema

def get_cluster_service(db: Session = Depends(get_cmp_db)):
    return ClusterService(db)

router = APIRouter(
    prefix="/cluster",
    tags=["集群列表"],
    dependencies=[Depends(require_user)],
)

#   cbs创建
@router.post("/cluster_create")
def cbs_create(
    # data: ClusterCreateSchema,
    data: dict,
    request: Request,
    service: ClusterService = Depends(get_cluster_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.create_cluster_full(request.state.user, data)
    return Response.success(result)

# 集群列表
@router.get("/clusters/page_list")
def cluster_page_list(
    request: Request,
    page: int = Query(..., description="页码"),
    page_size: int = Query(..., description="每页数量"),
    name: Optional[str] = Query(None, description="集群名称"),
    service: ClusterService = Depends(get_cluster_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.cluster_page_list(request.state.user, page, page_size, name)
    return Response.success(result)

# 节电池列表
@router.get("/clusters/pool/list")
def cluster_pool_list(
    cluster_id: int = Query(..., description="集群id"),
    service: ClusterService = Depends(get_cluster_service)
):
    result = service.cluster_pool_list(cluster_id)
    return Response.success(result)

# 节电列表
@router.get("/clusters/node/list")
def cluster_pool_list(
    cluster_id: int = Query(..., description="集群id"),
    pool_id: int = Query(None, description="节电池id"),
    service: ClusterService = Depends(get_cluster_service)
):
    result = service.cluster_node_list(cluster_id, pool_id)
    return Response.success(result)
