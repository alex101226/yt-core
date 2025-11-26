from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class InstanceTypeBase(BaseModel):
    instance_type_id: str
    instance_family: Optional[str] = None
    generation: Optional[str] = None

    cpu_core_count: Optional[int] = None
    memory_size: Optional[float] = None

    architecture: Optional[str] = None

    gpu_amount: Optional[int] = None
    gpu_spec: Optional[str] = None
    gpu_memory: Optional[float] = None

    local_storage_amount: Optional[int] = None
    local_storage_capacity: Optional[int] = None

    network_performance: Optional[str] = None
    is_io_optimized: Optional[bool] = True

    price: Optional[Decimal] = None

    cloud_provider_code: str

class InstanceTypeOut(InstanceTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

#   provider_code: 云厂商, region_id: 区域, zone_id: 可用区, instance_charge_type: 付费方式, cpu_number: cpu核数,
#   memory_number: 内存, gpu_spec: gpu规格, gpu_name: 规格名称, hide_soldout: , 隐藏售罄规格 page, page_size
class InstanceTypeSearch(BaseModel):
    provider_code: str
    region_id: str
    zone_id: str
    instance_charge_type: Optional[str] = None
    cpu_number: Optional[int] = None
    memory_number: Optional[int] = None
    gpu_spec: Optional[str] = None
    gpu_name: Optional[str] = None
    hide_soldout: bool = False
    page: int = 1
    page_size: int = 20