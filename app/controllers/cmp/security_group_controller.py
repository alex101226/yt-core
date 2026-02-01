from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleOut, SecurityGroupRuleUpdate, \
    SecurityGroupRuleItem
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
    request: Request,
    page: int = Query(...),
    page_size: int = Query(...),
    provider_code: str = Query(None, description="云厂商 code"),
    region_id: str = Query(None, description="区域 id"),
    resource_group_id: Optional[str] = Query(None, description="资源组"),
    sg_name: Optional[str] = Query(None, description="安全组 name"),
    service: SecurityGroupService = Depends(get_security_service),
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    # user_id = request.state.user.get('user_id')
    items =  service.list_page(parent_id, page, page_size, provider_code, region_id, resource_group_id, sg_name)
    return Response.success(items)

@router.post("/group_create", response_model=SecurityGroupOut)
def create_security_group(
    data: SecurityGroupCreate,
    request: Request,
    service: SecurityGroupService = Depends(get_security_service)
):
    # user_id = request.state.user.get('user_id')
    result = service.create(request.state.user, data)
    return Response.success(result)


@router.put("/group_release")
def release_security_group(
    group_id: int,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.release(group_id)
    return Response.success(result)


#   返回安全组列表
@router.get("/group_list", response_model=SecurityGroupPage)
def list_security_groups(
    request: Request,
    provider_code: str = Query(..., description="云厂商 code"),
    region_id: str = Query(..., description="区域 id"),
    vpc_id: int = Query(..., description="vpc的id"),
    service: SecurityGroupService = Depends(get_security_service),
):
    parent_id = request.state.user.get('parent_id') or 0
    if parent_id == 0:
        parent_id = request.state.user.get('user_id')
    items =  service.list_security_groups(parent_id, provider_code, region_id, vpc_id)
    return Response.success(items)

# 创建安全组时，批量创建规则
@router.put("/batch_rule_update")
def update_rules(
    request: Request,
    data: SecurityGroupRuleUpdate,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.batch_update_rules(data, request.state.user)
    return Response.success(result)

#   创建单条规则
@router.post('/rule_create', response_model=SecurityGroupOut)
def create_security_group_rule(
    request: Request,
    data: SecurityGroupRuleItem,
    service: SecurityGroupService = Depends(get_security_service)
):
    result = service.create_rule(data, request.state.user)
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