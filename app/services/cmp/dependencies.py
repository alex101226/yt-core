# app/services/public/dependencies
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_cmp_db
from app.common.dependencies import get_public_db
from app.services.cmp.vpc_service import VPCService

#   VPC Service 依赖注入
def get_vpc_service(
    cmp_db: Session = Depends(get_cmp_db),
    public_db: Session = Depends(get_public_db)
) -> VPCService:
     return VPCService(cmp_db, public_db)