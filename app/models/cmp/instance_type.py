from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, DECIMAL
from sqlalchemy.sql import func
from app.core.database import CmpBase
from app.core.config import settings


class InstanceType(CmpBase):
    __tablename__ = f"{settings.CMP_TABLE_PREFIX}instance_type"
    __table_args__ = {"comment": "多云厂商实例规格全量表（DescribeInstanceTypes 等接口同步）"}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")

    instance_type_id = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        comment="规格ID，例如 ecs.g7.large / S7.MEDIUM4(腾讯)/c6.large(AWS)"
    )

    instance_family = Column(
        String(64),
        index=True,
        comment="规格族，例如 ecs.g7 / c7 / m6a / S7"
    )

    generation = Column(
        String(32),
        index=True,
        comment="规格代次，例如 g7、g8、c7、c8（不同云厂商表示不同，仅供展示）"
    )

    cpu_core_count = Column(
        Integer,
        comment="vCPU 核数"
    )

    memory_size = Column(
        Float,
        comment="内存容量（GiB）"
    )

    architecture = Column(
        String(32),
        comment="CPU 架构：x86 或 arm"
    )

    gpu_amount = Column(
        Integer,
        comment="GPU 个数（无GPU的规格为0）"
    )

    gpu_spec = Column(
        String(64),
        comment="GPU 型号，如 NVIDIA A10、V100、T4；无GPU为空"
    )

    gpu_memory = Column(
        Float,
        comment="GPU 显存（GiB），无GPU为空"
    )

    local_storage_amount = Column(
        Integer,
        comment="本地盘数量（Local NVMe / SSD / HDD 数量）"
    )

    local_storage_capacity = Column(
        Integer,
        comment="本地盘容量（GiB，总容量）"
    )

    network_performance = Column(
        String(128),
        comment="网络性能信息，如带宽/ PPS / 网络等级（字段来源各云厂商有差异）"
    )

    is_io_optimized = Column(
        Boolean,
        default=True,
        comment="是否为 IO 优化实例（默认 True，适用于大部分厂商）"
    )

    price = Column(
        DECIMAL(10, 2),
        nullable=True,
        comment="参考价格（可选字段，不同云厂商可能数据来源不同）"
    )

    cloud_provider_code = Column(
        String(30),
        nullable=False,
        comment="云厂商标识，例如 aliyun、tencent、huawei、aws、gcp"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="创建时间"
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )