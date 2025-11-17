# app/services/public/dependencies
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.dependencies import get_public_db
from app.services.cmp.vpc_service import VPCService
from app.services.cmp.dict_service import DictService
from app.services.cmp.subnet_service import SubnetService

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


