from typing import List, Optional
from pydantic import BaseModel, Field

from app.constants.enums import (
    NetworkType, LBInstanceType, ListenerProtocol
)

# 创建负载均衡后端成员
class BackendMemberCreate(BaseModel):
    resource_type: str = Field(..., description="后端资源类型 server/cluster_node")
    resource_id: int = Field(..., description="后端资源ID")
    ip_address: str = Field(..., description="后端IP")
    port: int = Field(..., description="后端端口")
    weight: int = Field(default=100, description="权重")

# 创建负载均衡后端池
class BackendPoolCreate(BaseModel):
    name: str = Field(..., description="后端池名称")
    algorithm: str = Field(..., description="调度算法")
    backends: List[BackendMemberCreate]

# 创建负载均衡监听器
class ListenerCreate(BaseModel):
    lb_id: int = Field(..., description="监听器实例id")
    name: str = Field(..., description="监听器名称")
    protocol: ListenerProtocol = Field(..., description="监听协议")
    port: int = Field(..., description="监听端口")
    backend_port: int = Field(..., description="后端端口")
    backend_pool: BackendPoolCreate
    status: str = Field(..., description="监听器状态")

# 创建负载均衡实例
class LoadBalancerCreate(BaseModel):
    lb_name: str = Field(..., description="负载均衡名称")

    # 归属 / 资源管理
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    cloud_provider_code: str = Field(..., description="云厂商")

    # 网络位置
    region_id: str = Field(..., description="区域ID")
    vpc_id: int = Field(None, description="VPC ID")
    subnet_id: int = Field(None, description="子网ID")

    # 计费 & 规格
    charge_type: str = Field(..., description="计费方式：按量 / 包年包月")
    instance_model: str = Field(..., description="实例型号")
    bandwidth: Optional[int] = Field(..., description="带宽上限")

    # 网络属性
    network_type: NetworkType = Field(..., description="公网 / 私网")

    # 元数据
    tags: Optional[list[str]] = Field(default_factory=list, description="标签")
    description: Optional[str] = Field(None, description="描述")

    price: float = 0

# 负载均衡-访问控制
class LoadBalancerACLCreate(BaseModel):
    acl_name: str
    resource_group_id: Optional[int]
    cloud_provider_code: str
    region_id: str
    source_cidr: str  # 👈 多行文本
    description: Optional[str] = None

class LoadCertificateCreate(BaseModel):
    cert_name: str = Field(..., description="证书名称")
    resource_group_id: Optional[int] = Field(None, description="资源组ID")
    cloud_provider_code: str = Field(..., description="云厂商编码")
    region_id: str = Field(..., description="区域ID")
    cert_content: str = Field(..., description="证书内容")
    cert_key: str = Field(..., description="证书密钥")
    tags: Optional[List[str]] = Field(None, description="标签")
    description: Optional[str] = Field(None, description="备注")
