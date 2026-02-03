from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List


class BareMetalInstanceBase(BaseModel):
    instance_name: str  # 服务器名称
    description: Optional[str] = None   # 描述

    cloud_provider_code: str    # 云厂商
    region_id: str   # 区域
    zone_id: str    # 可用区
    resource_group_id: int  # 资源组

    instance_type: str  # 实例规格类型，接口：/cloud/spec_page_list, 字段 instance_family: "ecs.g8ine"
    instance_type_id: Optional[str] # 实例规格id，接口：/cloud/spec_page_list, 字段：instance_type_id
    image_id: str    # 镜像id，接口：/cloud/images，字段：image_id
    cpu: Optional[int] = 0  # cpu核数：接口：/cloud/spec_page_list, 字段 cpu_core_count
    gpu_memory: Optional[int] = 0   # GPU 显存：接口：/cloud/spec_page_list, 字段 gpu_memory
    gpu_amount: Optional[int] = 0    # GPU 数量：接口：/cloud/spec_page_list, 字段 gpu_amount
    gpu_spec: Optional[str] = None  # GPU类型：接口：/cloud/spec_page_list, 字段 gpu_spec
    system_disk_category: str   # 系统盘类型：接口：cloud/system_disk_categories
    system_disk_size: int   # 系统盘类型：接口：cloud/spec_page_list，字段：memory_size

    # internet_charge_type: Optional[str] # 带宽的 PayByBandwidth/PayByTraffic
    charge_type: str  # 实例规格计费，PrePaid（包年包月） / PostPaid（按量付费）
    auto_renew: Optional[bool] = False  # 是否自动续费，instance_charge_type=PrePaid，bool值
    period: Optional[int] = 1    # instance_charge_type=PrePaid，传递选择的月份，整数
    quantity: Optional[int] = 1 # 服务器数量
    # internet_max_bandwidth_out: Optional[int]

    vpc_id: int # 选择的vpc的id
    vswitch_id: int # 选择的子网的id
    security_group_id: str  # 选择的安全组的id
    # ssh_proxy_port: Optional[int] = 0     #   SSH 代理端口

    os_type: Optional[str] = None    # 操作系统：接口：/cloud/images，字段：os_type
    architecture: Optional[str] = None  # cpu的架构：接口：/cloud/images，字段：architecture
    hostname: Optional[str] = None  # 主机名，输入的
    price: Optional[float] = 0.00

class BareMetalInstanceCreate(BareMetalInstanceBase):
    password: str   # 密码
    # cidr_block: Optional[str]  # 子网的网段，要计算private_ip的ip
    # enable_protection: Optional[bool] = False   # 是否开启释放保护
    install_gpu_driver: Optional[bool] = False  # 是否安装gpu驱动
    enable_ssh_agent: Optional[bool] = False     # 是否开启 SSH 代理
    pass

class BareMetalInstanceOut(BareMetalInstanceBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_released: Optional[bool] = False
    sync_status: Optional[int] = 0
    released_at: Optional[datetime] = None
    status: Optional[str] = None
    enable_protection: Optional[bool] = False  # 是否开启释放保护
    enable_ssh_agent: Optional[bool] = False  # 是否开启 SSH 代理

    class Config:
        from_attributes = True

class BareMetalInstancePage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BareMetalInstanceOut]

# 开机，关机，重启
class BareActionSchema(BaseModel):
    status: str
    instance_id: int

class BareUpdatePassword(BaseModel):
    password: str
    instance_id: int

#   转包年月
class BareUpdateCharge(BaseModel):
    instance_id: int
    charge_type: str  # 实例规格计费，PrePaid（包年包月） / PostPaid（按量付费）
    period: Optional[int] = 1  # instance_charge_type=PrePaid，传递选择的月份，整数
    auto_renew: Optional[bool] = False  # 包年月，是否自动续费