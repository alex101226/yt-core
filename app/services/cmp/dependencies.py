# app/services/public/dependencies
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.dependencies import (get_public_db, get_cmp_db)
from app.services.cmp.dict_service import DictService

from app.services.cmp.vpc_service import VPCService
from app.services.cmp.subnet_service import SubnetService
from app.services.cmp.security_group_service import SecurityGroupService
from app.services.cmp.security_group_rule_service import SecurityGroupRuleService

#   字典
def get_dict_service(
   db: Session = Depends(get_cmp_db),
):
    return DictService(db)


#   VPC Service 依赖注入
def get_vpc_service(
    cmp_db: Session = Depends(get_cmp_db),
    public_db: Session = Depends(get_public_db)
) -> VPCService:
     return VPCService(cmp_db, public_db)

# Subnet Service 依赖注入
def get_subnet_service(
    cmp_db: Session = Depends(get_cmp_db),
    public_db: Session = Depends(get_public_db)
) -> SubnetService:
    return SubnetService(cmp_db, public_db)

# 安全组
def get_security_service(
    cmp_db: Session = Depends(get_cmp_db),
    public_db: Session = Depends(get_public_db)
) -> SecurityGroupService:
    return SecurityGroupService(cmp_db, public_db)


# 安全组规则配置
def get_security_rule_service(
   db: Session = Depends(get_cmp_db)
) -> SecurityGroupRuleService:
    return SecurityGroupRuleService(db)

