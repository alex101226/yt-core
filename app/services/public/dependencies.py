# app/services/public/dependencies
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.dependencies import get_public_db
from app.services.public.resource_group_service import ResourceGroupService
from app.services.public.resource_group_binding_service import ResourceGroupBindingService
from app.services.public.cloud_certificate_service import CloudCertificateService
from app.services.public.cloud_provider_service import CloudProviderService
from app.services.public.cloud_region_service import CloudRegionService
from app.services.public.cloud_zone_service import CloudZoneService

#   云厂商
def get_cloud_provider_service(db: Session = Depends(get_public_db)) -> CloudProviderService:
    return CloudProviderService(db)

#   云厂商区域
def get_cloud_region_service(db: Session = Depends(get_public_db)) -> CloudRegionService:
    return CloudRegionService(db)

#   云厂商区域可用区
def get_cloud_zone_service(db: Session = Depends(get_public_db)) -> CloudZoneService:
    return CloudZoneService(db)

#   用户云凭证
def get_cloud_certificate_service(db: Session = Depends(get_public_db)) -> CloudCertificateService:
    return CloudCertificateService(db)

#   资源组
def get_resource_group_service(db: Session = Depends(get_public_db)) -> ResourceGroupService:
    return ResourceGroupService(db)

#   绑定资源组
def get_resource_group_binding_service(
    db: Session = Depends(get_public_db),
) -> ResourceGroupBindingService:
    return ResourceGroupBindingService(db)
