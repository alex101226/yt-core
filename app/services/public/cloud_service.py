from sqlalchemy.orm import Session

from typing import List, Optional
from app.clients.cloud_client_factory import CloudClientFactory
from app.repositories.public.cloud_region_repo import CloudRegionRepository
from app.repositories.public.cloud_zone_repo import CloudZoneRepository
from app.repositories.public.cloud_provider_repo import  CloudProviderRepository
from app.repositories.cmp.vpc_repo import VpcRepository
from app.repositories.cmp.subnet_repo import SubnetRepository
from app.repositories.cmp.instance_type_repo import InstanceTypeRepo

from app.schemas.public.cloud_region_schema import CloudRegionBase
from app.schemas.public.cloud_zone_schema import CloudZoneList
from app.schemas.cmp.vpc_schema import VpcBase
from app.schemas.cmp.subnet_schema import SubnetBase
from app.schemas.cmp.instance_type_schema import InstanceTypeBase

from app.core.logger import logger

class CloudService:
    def __init__(self, db: Session, provider_code: str, access_key_id: str, access_key_secret: str, endpoint: str):
        self.db = db
        self.provider_code = provider_code
        self.client = CloudClientFactory.create_client(provider_code, access_key_id, access_key_secret, endpoint)
        self.provider_repo = CloudProviderRepository(db)

        self.region_repo = CloudRegionRepository(db)
        self.zone_repo = CloudZoneRepository(db)
        self.vpc_repo = VpcRepository(db)
        self.subnet_repo = SubnetRepository(db)
        self.instance_type_repo = InstanceTypeRepo(db)

    def list_regions(self) -> List[CloudRegionBase]:
        db_regions = self.region_repo.region_list(self.provider_code)
        if db_regions:
            return [
                CloudRegionBase(
                    provider_code=self.provider_code,
                    region_id=r.region_id,
                    region_name=r.region_name
                ) for r in db_regions
            ]

        regions = self.client.list_regions()
        self.region_repo.bulk_upsert(self.provider_code, regions)
        return regions

    def list_zones(self, provider_code: str, region_id: str) -> List[CloudZoneList]:
        db_zones = self.zone_repo.get_by_zones(provider_code, region_id)
        if db_zones:
            return [
                CloudZoneList(
                    id=z.id,
                    provider_code=z.provider_code,
                    region_id=z.region_id,
                    zone_id=z.zone_id,
                    zone_name=z.zone_name
                ) for z in db_zones
            ]
        zones = self.client.list_zones(region_id)
        self.zone_repo.bulk_upsert(provider_code, region_id, zones)
        return zones

    def list_vpcs(self, provider_code: str, region_id: str) -> List[VpcBase]:
        db_vpcs = self.vpc_repo.get_by_vpcs(provider_code, region_id)
        if db_vpcs:
            return [
                VpcBase(
                    vpc_name=v.vpc_name,
                    description=v.description,
                    region_id=v.region_id,
                    resource_group_id=v.resource_group_id,
                    cloud_provider_code=v.cloud_provider_code,
                    cloud_certificate_id=v.cloud_certificate_id,
                    network_type=v.network_type
                ) for v in db_vpcs
            ]
        vpcs = self.client.list_vpcs(region_id)
        self.vpc_repo.bulk_upsert(provider_code, region_id, vpcs)
        return vpcs


    def list_vswitches(self, provider_code, region_id: str, vpc_id: str) -> List[SubnetBase]:
        db_subnet = self.subnet_repo.list_by_subnet(vpc_id)
        if db_subnet:
            return [
                SubnetBase(
                    subnet_name=s.subnet_name,
                    description=s.description,
                    vpc_id=s.vpc_id,
                    resource_group_id=s.resource_group_id,
                    cloud_provider_code=s.cloud_provider_code,
                    cloud_certificate_id=s.cloud_certificate_id,
                    region_id=s.region_id,
                    zone_id=s.zone_id,
                    cidr_block=s.cidr_block
                ) for s in db_subnet
            ]

        subnets = self.client.list_vswitches(region_id, vpc_id)
        self.subnet_repo.bulk_upsert(provider_code, region_id, vpc_id, subnets)
        return subnets

    def list_images(self, region_id: str) -> List[dict]:
        images = self.client.list_images(region_id)
        return images

    def list_instance_types(self, provider_code: str):
        db_instance_type = self.instance_type_repo.get_by_instance_type(provider_code)
        if db_instance_type:
            return [
                InstanceTypeBase.model_validate(i, from_attributes=True) for i in db_instance_type
            ]

        instance_types = self.client.list_instance_types(provider_code)
        self.instance_type_repo.bulk_upsert(provider_code, instance_types)
        return instance_types

    def list_available_type(self, region_id: str, zone_id: str, include_soldout: bool = False) -> List[dict]:
        return self.client.list_available_instance_types(region_id, zone_id, include_soldout)

    def list_pricing(self, region_id, instance_type, charge_type=Optional[str], period: Optional[int] = None) -> List[dict]:
        return self.client.list_pricing_options(region_id, instance_type, charge_type, period)