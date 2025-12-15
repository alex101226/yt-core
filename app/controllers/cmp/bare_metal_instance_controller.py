from fastapi import APIRouter, Depends, Request, Query
from typing import Optional, List
from enum import Enum
from sqlalchemy.orm import Session

from app.common.response import Response
from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user

from app.schemas.cmp.bare_metal_instance_schema import BareMetalInstanceCreate
from app.services.cmp.bare_metal_instance_service import BareMetalInstanceService

def get_bare_service(
   db: Session = Depends(get_cmp_db),
):
    return BareMetalInstanceService(db)

router = APIRouter(prefix="/bare_metal_instance", tags=["裸金属"], dependencies=[Depends(require_user)])

# 创建裸金属
@router.post("/server_create")
def create_instance(
    request: Request,
    data: BareMetalInstanceCreate,
    service: BareMetalInstanceService = Depends(get_bare_service)):

    user_id = request.state.user.get('user_id')
    instance = service.bare_metal_instance_create(user_id, data)

    # result = {
    #     "id": instance.id,
    #     "instance_name": instance.instance_name,
    #     "status": instance.status,
    #     "resource_group_id": instance.resource_group_id
    # }
    return Response.success(instance)

