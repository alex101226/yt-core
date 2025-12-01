# app/schemas/cmp/instance.py
from pydantic import BaseModel
from typing import List, Optional

class DiskItem(BaseModel):
    disk_category: str
    disk_size: int
    encrypted: Optional[bool] = False

class InstanceBase(BaseModel):
    cloud_provider_code: str
    region_id: str
    zone_id: Optional[str]
    instance_name: str
    instance_type: str
    image_id: str
    system_disk_category: str
    system_disk_size: int

    instance_charge_type: str  # PrePaid / PostPaid
    period: Optional[int]
    spot_strategy: Optional[str]

    internet_charge_type: Optional[str]
    internet_max_bandwidth_out: Optional[int]

    vpc_id: Optional[str]
    vswitch_id: Optional[str]
    # cidr_block: Optional[str]  # 子网的网段，要计算private_ip的ip
    security_group_id: Optional[str]

    hostname: Optional[str]
    description: Optional[str]
    password: Optional[str]
    key_pair_name: Optional[str]
    enable_ssh_agent: Optional[bool] = False
    enable_protection: Optional[bool] = False
    resource_group_id: Optional[int]  # 资源组
    data_disks: Optional[List[DiskItem]] = []

class InstanceCreateSchema(InstanceBase):
    pass


class InstanceBaseOut(InstanceBase):
    id: int
    pass

    class Config:
        from_attributes = True


class InstancePage(InstanceBase):
    total: int
    page: int
    page_size: int
    items: List[InstanceBaseOut]