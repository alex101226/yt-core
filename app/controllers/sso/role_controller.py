from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db
from app.common.response import Response

from app.services.sso.role_service import RoleService
from app.schemas.sso.role_schema import RoleAddSchema

def get_role_service( db: Session = Depends(get_sso_db)):
  return RoleService(db)

router = APIRouter(prefix="/role", tags=["用户角色"])

@router.get("/list")
def role_list(service: RoleService = Depends(get_role_service)):
    roles = service.role_list()
    return Response.success(roles)

@router.post('/create')
def role_create(
    data: RoleAddSchema,
    service: RoleService = Depends(get_role_service)
):
    result = service.role_create(data)
    return Response.success(result)