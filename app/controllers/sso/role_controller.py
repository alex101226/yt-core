from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.orm import Session

from app.common.dependencies import get_sso_db
from app.common.response import Response

from app.services.sso.role_service import RoleService
from app.schemas.sso.role_schema import RoleAddSchema, RoleUpdateSchema

def get_role_service( db: Session = Depends(get_sso_db)):
  return RoleService(db)

router = APIRouter(prefix="/role", tags=["用户角色"])

@router.get("/list")
def role_list(service: RoleService = Depends(get_role_service)):
    roles = service.role_list()
    return Response.success(roles)

@router.get("/page_list")
def role_page_list(
    page: int = Query(..., description="分页"),
    page_size: int = Query(..., description="每页条数"),
    role_name: str = Query(None, description="角色名称"),
    service: RoleService = Depends(get_role_service)
):
    result = service.role_page_list(page, page_size, role_name)
    return Response.success(result)

@router.post('/create')
def role_create(
    data: RoleAddSchema,
    service: RoleService = Depends(get_role_service)
):
    result = service.role_create(data)
    return Response.success(result)


@router.put('/update')
def role_update(
    data: RoleUpdateSchema,
    service: RoleService = Depends(get_role_service)
):
    result = service.role_update(data)
    return Response.success(result)

@router.delete('/delete')
def role_delete(
    role_id: int = Query(..., description="角色ID"),
    service: RoleService = Depends(get_role_service)
):
    result = service.role_delete(role_id)
    return Response.success(result)
