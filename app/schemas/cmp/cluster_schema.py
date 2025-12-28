from pydantic import BaseModel, Field
from typing import List, Optional

# -------------------
# 集群 创建 DTO
# -------------------
class ClusterCreateSchema(BaseModel):
    cluster_name: str = Field(..., description="集群名称")
    region_id: str = Field(..., description="区域")
    zone_id: str = Field(..., description="可用区")
    provider_code: str = Field(..., description="云厂商")
    resource_group_id: int = Field(..., description="资源组")
    charge_type: str = Field(..., description="计费方式，POSTPAID/ PREPAID")
    period: Optional[int] = Field(None, description="包年包月月份")
    auto_renew: Optional[bool] = Field(False, description="是否自动续费")
    cluster_spec: str = Field(..., description="集群规格")
    master_count: int = Field(1, description="master节点数量")
    cluster_version: str = Field(..., description="集群版本")
    network_type: str = Field(..., description="网络类型")
    vpc_id: int = Field(..., description="VPC ID")
    subnet_ids: List[str] = Field(..., description="IP 子网ID")
    security_group_id: str = Field(..., description="安全组ID")
    service_cidr: str = Field(..., description="服务网段")
    deletion_protection: bool = Field(False, description="删除保护")
    tags: Optional[List[str]] = Field(None, description="集群标签")

    node_pools: List['NodePoolCreateSchema'] = Field(..., description="节点池列表")


# -------------------
# 节点池 创建 DTO
# -------------------
class NodePoolCreateSchema(BaseModel):
    pool_name: str = Field(..., description="节点池名称")
    node_type: str = Field(..., description="节点类型 ECS/BMS")
    charge_type: str = Field(..., description="计费方式")
    period: Optional[int] = Field(None, description="包年包月月数")
    auto_renew: Optional[bool] = Field(False, description="是否自动续费")
    # instance_types: List[dict] = Field(..., description="节点池实例规格列表")
    desired_size: int = Field(..., description="期望节点数")
    min_size: int = Field(..., description="最小节点数")
    max_size: int = Field(..., description="最大节点数")
    scaling_policy: str = Field(..., description="扩缩容策略")
    auto_repair: Optional[bool] = Field(True, description="异常节点自动替换")
    image_id: str = Field(..., description="系统镜像ID")
    system_disk_type: str = Field(..., description="系统盘类型")
    system_disk_size: int = Field(..., description="系统盘大小（GB）")
    admin_password: Optional[str] = Field(None, description="管理员密码")
    labels: Optional[List[str]] = Field(None, description="节点池标签")
    taints: Optional[List[str]] = Field(None, description="污点配置")

# -------------------
# 节点 创建
# -------------------
class NodeCreateSchema(BaseModel):
    cluster_id: int = Field(..., description="所属集群id")
    node_pool_id: int = Field(..., description="所属节点池ID")
    node_id: int = Field(..., description="节点id，唯一")
    instance_id: str = Field(..., description="节点实例ID")
    # node_name: str = Field(..., description="节点名称")
    # instance_type: str = Field(..., description="节点规格")
    os_image: str = Field(..., description="镜像")
    cluster_node_role: str = Field(..., description="节点角色，字典：CLUSTER_NODE_ROLE")
    # status: str = Field("CREATING", description="节点状态，字典：NODE_STATUS")
    cordon: bool = Field(False, description="是否禁止调度（cordon）")
    drain: bool = Field(False, description="是否已驱逐Pod（drain）")
    labels: Optional[List[str]] = Field(None, description="节点标签")

