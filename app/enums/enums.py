from enum import Enum

# 字典表的type_code，接口调试
class DictType(str, Enum):
    SERVER_STATUS = "SERVER_STATUS"
    NETWORK_TYPE = "NETWORK_TYPE"
    TASK_STATUS="TASK_STATUS"
    EIP_STATUS="EIP_STATUS"

# eip的操作状态，接口调试
class EipStatus(str, Enum):
    RELEASING = "RELEASING" # 释放
    BINDING = "BINDING" # 绑定
    UNBINDING = "UNBINDING" # 解绑

# cbs盘类型，system=系统盘，data=数据盘，接口调试
class DiskType(str, Enum):
    SYSTEM = "system"
    DATA = "data"

# 磁盘类型，接口调试
class DiskCategory(str, Enum):
    ESSD_PL0 = "ESSD_PL0"
    ESSD_PL1 = "ESSD_PL1"
    ESSD_PL2 = "ESSD_PL2"
    SSD = "SSD"
    PREMIUM_SSD = "PREMIUM_SSD"
    CLOUD_EFFICIENCY = "CLOUD_EFFICIENCY"
    CLOUD_HDD = "CLOUD_HDD"

# 除了宽带的付费类型，PrePaid=按量，PostPaid=包年月，接口调试
class ChargeType(str, Enum):
    PREPAID = "PrePaid"
    POSTPAID = "PostPaid"

# cbs盘的状态，主要用于接口调试方便
class DiskStatus(str, Enum):
    CREATING = "Creating"
    AVAILABLE = "Available"
    IN_USE = "InUse"
    ATTACHING = "Attaching"
    DETACHING = "Detaching"
    RECYCLING = "Recycling"
    DELETED = "Deleted"
