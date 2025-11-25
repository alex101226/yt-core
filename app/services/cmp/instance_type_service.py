from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.cmp.instance_type import InstanceType
from app.services.public.cloud_service import CloudService

from app.repositories.public.cloud_provider_repo import CloudProviderRepository

from app.repositories.cmp.instance_type_repo import InstanceTypeRepo

from app.schemas.cmp.instance_type_schema import InstanceTypeSearch, InstanceTypeBase

from app.core.logger import logger

class InstanceTypeService:
    def __init__(self, cmp_db: Session, public_db: Session):
        self.db = cmp_db
        self.instance_type_repo = InstanceTypeRepo(cmp_db)
        self.provider_repo = CloudProviderRepository(public_db)

    #   全量的类型
    def list_instance_types(self, provider_code: str):
        provider = self.provider_repo.get_by_code(provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client_region = CloudService(
            self.db,
            provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        instance_types = client_region.list_instance_types(provider_code)
        return instance_types

    def full_instance_table(self, type_id: str) -> Optional[type[InstanceType]]:
        data = self.instance_type_repo.get_by_instance_type_find(type_id)
        if not data:
            return None
        return data
    #   可用区
    # provider_code: str,
    # region_id: str,
    # zone_id: str,
    # charge_type: str = "PostPaid",
    # min_cpu: Optional[int] = None,
    # min_memory: Optional[str] = None,
    # gpu_spec: Optional[str] = None,
    # name_like: Optional[str] = None,
    # hide_soldout: bool = True,
    # page: int = 1,
    # page_size: int = 20
    def list_available_instance_types(
        self,
        search: InstanceTypeSearch
       ):

        provider = self.provider_repo.get_by_code(search.provider_code)
        if not provider:
            raise BusinessException(
                code=ErrorCode.DATA_NOT_FOUND,
                message=Message.DATA_NOT_FOUND
            )

        # 2️⃣ 根据厂商类型创建客户端
        client = CloudService(
            self.db,
            search.provider_code,
            provider.access_key_id,
            provider.access_key_secret,
            provider.endpoint,
        )

        available_list = client.list_available_type(
            search.region_id,
            search.zone_id,
            include_soldout=not search.hide_soldout
        )
        instance_all = []
        for available in available_list:
            type_id = available.get('instance_type_id')
            inst = self.full_instance_table(type_id)
            price = client.list_pricing(
                search.region_id,
                type_id,
            )
            if price:
                instance_all.append({
                    "instance_type_id": available['instance_type_id'],
                    "price": price.get("instancetype", 0),
                    # "cpu_core_count": inst.cpu_core_count,
                    # "gpu_amount": inst.gpu_amount,
                    # "gpu_spec": inst.gpu_spec,
                    # "gpu_memory": inst.gpu_memory,
                    "zone_id": search.zone_id,
                    # "architecture": inst.architecture,
                    # "memory_size": inst.memory_size,
                })
        return instance_all