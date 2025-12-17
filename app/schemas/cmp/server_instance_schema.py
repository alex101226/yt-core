# app/schemas/cmp/instance.py
from pydantic import BaseModel
from typing import List, Optional

class DiskItem(BaseModel):
    disk_category: str
    disk_size: int
    encrypted: Optional[bool] = False

class InstanceBase(BaseModel):
    instance_name: str
    description: Optional[str] = None

    cloud_provider_code: str
    region_id: str
    zone_id: str
    resource_group_id: Optional[int]  # 资源组

    instance_type: Optional[str] = None
    instance_type_id: Optional[str]

    image_id: str
    cpu: Optional[int] = 0
    gpu_memory: Optional[int] = 0
    gpu_amount: Optional[int] = 0
    gpu_spec: Optional[str] = None
    system_disk_category: str
    system_disk_size: int

    instance_charge_type: str  # PrePaid / PostPaid
    period: Optional[int] = 0
    spot_strategy: Optional[str] = None
    internet_charge_type: Optional[str] = None
    internet_max_bandwidth_out: Optional[int] = 0

    vpc_id: int
    vswitch_id: int
    security_group_id: str
    ssh_proxy_port: Optional[int] = 0

    data_disks: Optional[List[DiskItem]] = []

    os_type: Optional[str] = None
    architecture: Optional[str] = None
    hostname: Optional[str] = None

class InstanceCreateSchema(InstanceBase):
    cidr_block: Optional[str]  # 子网的网段，要计算private_ip的ip
    password: Optional[str]
    enable_protection: Optional[bool] = False
    enable_ssh_agent: Optional[bool] = False
    pass


class InstanceBaseOut(InstanceBase):
    id: int
    instance_id: str
    public_ip: Optional[str]
    private_ip: Optional[str]
    status: Optional[str]
    sync_status: Optional[int]
    enable_ssh_agent: Optional[bool] = False
    enable_protection: Optional[bool] = False
    pass

    class Config:
        from_attributes = True


class InstancePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[InstanceBaseOut]

# 开机，关机，重启
class InstanceActionSchema(BaseModel):
    status: str
    instance_id: int

class InstanceUpdatePassword(BaseModel):
    password: str
    instance_id: int