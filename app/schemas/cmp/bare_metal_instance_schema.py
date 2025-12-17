from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List


class BareMetalInstanceBase(BaseModel):
    instance_name: str
    description: Optional[str] = None

    cloud_provider_code: str
    region_id: str
    zone_id: str
    resource_group_id: int

    instance_type: str
    instance_type_id: Optional[str]
    image_id: str
    cpu: Optional[int] = 0
    gpu_memory: Optional[int] = 0
    gpu_amount: Optional[int] = 0
    gpu_spec: Optional[str] = None
    system_disk_category: str
    system_disk_size: int

    internet_charge_type: Optional[str] # PayByBandwidth/PayByTraffic
    instance_charge_type: str  # PrePaid / PostPaid
    period: Optional[int] = 1
    quantity: Optional[int] = 1
    internet_max_bandwidth_out: Optional[int]
    auto_renew: Optional[bool] = False

    vpc_id: int
    vswitch_id: int
    security_group_id: str
    ssh_proxy_port: Optional[int] = 0

    os_type: Optional[str] = None
    architecture: Optional[str] = None
    hostname: Optional[str] = None

class BareMetalInstanceCreate(BareMetalInstanceBase):
    password: str
    cidr_block: Optional[str]  # 子网的网段，要计算private_ip的ip
    enable_protection: Optional[bool] = False
    install_gpu_driver: Optional[bool] = False
    enable_ssh_agent: Optional[bool] = False
    pass

class BareMetalInstanceOut(BareMetalInstanceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_released: Optional[bool] = False
    sync_status: Optional[int] = 0
    released_at: Optional[datetime] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class BareMetalInstancePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BareMetalInstanceOut]