from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.services.cmp.dependencies import get_security_rule_service
from app.services.cmp.security_group_rule_service import SecurityGroupRuleService
from app.schemas.cmp.security_group_rule_schema import SecurityGroupRuleUpdate, SecurityGroupRuleOut
from app.common.response import Response

router = APIRouter(prefix="/security_group_rule", tags=["安全组规则配置"])


@router.put("/update")
def update_rules(
    data: SecurityGroupRuleUpdate,
    service: SecurityGroupRuleService = Depends(get_security_rule_service)
):
    result = service.update_rules(data)
    return Response.success(result)


@router.get("/list/{security_group_id}", response_model=SecurityGroupRuleOut)
def list_rules(
    security_group_id: str,
    service: SecurityGroupRuleService = Depends(get_security_rule_service)
):
    items = service.list_rules(security_group_id)
    return Response.success(items)

@router.delete("/delete")
def delete_rules(
    rule_id: str,
    service: SecurityGroupRuleService = Depends(get_security_rule_service)
):
    deleted_id = service.delete_rules(rule_id)
    return Response.success(deleted_id)
