from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.response import Response
from app.core.dependencies import require_user

from app.schemas.cmp.eip_schema import EIPSchema, EIPCreate
from app.services.cmp.eip_service import EIPService

def get_eip_service(db: Session = Depends(get_cmp_db)):
    return EIPService(db)

router = APIRouter(
    prefix="/eip",
    tags=["弹性公网"],
    dependencies=[Depends(require_user)]
)

#   创建eip
@router.post("/group_create")
def create_eip(
    data: EIPCreate,
    request: Request,
    service: EIPService = Depends(get_eip_service)
):
    user_id = request.state.user.get('user_id')
    result = service.create_eip(user_id, data)
    return Response.success(result)

