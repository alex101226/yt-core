from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleOut, SecurityGroupRuleUpdate
from app.schemas.cmp.security_group_schema import SecurityGroupPage, SecurityGroupOut, SecurityGroupCreate
from app.services.cmp.security_group_service import SecurityGroupService
from app.common.response import Response

from app.common.dependencies import get_cmp_db
from app.core.dependencies import require_user


def get_security_service(db: Session = Depends(get_cmp_db)):
    return SecurityGroupService(db)

router = APIRouter(
    prefix="/security_groups",
    tags=["安全组"],
    dependencies=[Depends(require_user)]
)

@router.get("/group_list_page", response_model=SecurityGroupPage)
def list_security_groups(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-qingdao', description="区域 id"),
    resource_group_id: Optional[int] = Query(None, description="资源组"),
    security_name: Optional[str] = Query(None, description="安全组 name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=200),
    service: SecurityGroupService = Depends(get_security_service),
):
    items =  service.list_page(provider_code, region_id, resource_group_id, security_name, page, page_size)
    return Response.success(items)

@router.post("/group_create", response_model=SecurityGroupOut)
def create_security_group(
    data: SecurityGroupCreate,
    request: Request,
    service: SecurityGroupService = Depends(get_security_service)
):
    user_id = request.state.user.get('user_id')
    payload = data.model_dump()
    payload['user_id'] = user_id
    result = service.create(payload)
    return Response.success(result)


@router.post("/group_release")
def release_security_group(
    groud_id: str,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.release(groud_id)
    return Response.success(result)


#   返回安全组列表
@router.get("/group_list", response_model=SecurityGroupPage)
def list_security_groups(
    provider_code: str = Query('aliyun', description="云厂商 code"),
    region_id: str = Query('cn-qingdao', description="区域 id"),
    vpc_id: int = Query(None, description="vpc的id"),
    service: SecurityGroupService = Depends(get_security_service),
):

    items =  service.list_security_groups(provider_code, region_id, vpc_id)
    return Response.success(items)

@router.put("/rule_update")
def update_rules(
    data: SecurityGroupRuleUpdate,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.update_rules(data)
    return Response.success(result)


@router.get("/rule_list/{security_group_id}", response_model=SecurityGroupRuleOut)
def list_rules(
    security_group_id: str,
    service: SecurityGroupService = Depends(get_security_service)
):
    items = service.list_rules(security_group_id)
    return Response.success(items)

@router.delete("/rule_delete")
def delete_rules(
    rule_id: str,
    service: SecurityGroupService = Depends(get_security_service)
):
    deleted_id = service.delete_rules(rule_id)
    return Response.success(deleted_id)