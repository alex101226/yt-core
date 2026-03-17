from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class StudioListItemSchema(BaseModel):
    id: int
    studio_name: str
    instance_id: str
    studio_type: str
    resource_group_name: Optional[str] = None
    creator_name: Optional[str] = None
    region_display: str
    kubernetes_version: str
    created_at: datetime
    gpu_count: int
    cpu_usage_rate: float
    gpu_usage_rate: float
    memory_usage_rate: float
    healthy_node_count: int
    total_node_count: int
    enabled: bool
    status: str


class StudioPageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[StudioListItemSchema]


class StudioOptionSchema(BaseModel):
    id: int
    studio_name: str


class StudioMetricRingSchema(BaseModel):
    cpu_usage_rate: float
    gpu_usage_rate: float
    memory_usage_rate: float


class StudioTrendSeriesSchema(BaseModel):
    labels: List[str]
    cpu_usage_rate: List[float]
    gpu_usage_rate: List[float]
    memory_usage_rate: List[float]


class StudioNodeTrendItemSchema(BaseModel):
    node_id: int
    node_name: str
    cpu_usage_rate: List[float]
    gpu_usage_rate: List[float]
    memory_usage_rate: List[float]


class StudioNodeTrendSchema(BaseModel):
    labels: List[str]
    items: List[StudioNodeTrendItemSchema]


class StudioGpuUsageItemSchema(BaseModel):
    studio_name: str
    node_name: str
    gpu_status: str
    gpu_model: Optional[str] = None
    gpu_count: int
    gpu_memory_total: float
    gpu_memory_used: float


class StudioOverviewSchema(BaseModel):
    studio_count: int
    studio_normal_text: str
    node_normal_text: str
    metrics: StudioMetricRingSchema
    studio_monitor: StudioTrendSeriesSchema
    node_monitor: StudioNodeTrendSchema
    gpu_usages: List[StudioGpuUsageItemSchema]


class StudioNodeItemSchema(BaseModel):
    id: int
    studio_id: int
    node_name: str
    studio_name: str
    spec: str
    node_type: str
    status: str
    private_ip: Optional[str] = None
    vcpu_total: int
    vcpu_usage_rate: float
    memory_total_gb: float
    memory_usage_rate: float
    gpu_display: str
    charge_type: Optional[str] = None
    created_by_name: Optional[str] = None
    created_at: datetime


class StudioNodePageSchema(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[StudioNodeItemSchema]
