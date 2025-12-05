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
    zone_id: str
    resource_group_id: Optional[int]  # 资源组
    instance_type_id: Optional[str]
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
    vpc_id: str
    vswitch_id: str
    security_group_id: Optional[str]
    hostname: Optional[str]
    description: Optional[str]
    data_disks: Optional[List[DiskItem]] = []
    os_type: Optional[str]

class InstanceCreateSchema(InstanceBase):
    cidr_block: Optional[str]  # 子网的网段，要计算private_ip的ip
    password: Optional[str]
    key_pair_name: Optional[str]
    enable_ssh_agent: Optional[bool] = False
    enable_protection: Optional[bool] = False
    pass


class InstanceBaseOut(InstanceBase):
    id: int
    public_ip: Optional[str]
    private_ip: Optional[str]
    pass

    class Config:
        from_attributes = True


class InstancePage(InstanceBase):
    total: int
    page: int
    page_size: int
    items: List[InstanceBaseOut]