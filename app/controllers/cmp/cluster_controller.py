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
@router.post("/cbs_create")
def cbs_create(
    data: ClusterCreateSchema,
    request: Request,
    service: ClusterService = Depends(get_cluster_service)
):
    user_id = request.state.user.get('user_id')
    result = service.create_cluster_full(user_id, data)
    return Response.success(result)

