import enum

# 计费资源type
class ResourceType(enum.Enum):
    SERVER = "SERVER"   # 服务器
    DISK = "DISK"   # 磁盘
    EIP = "EIP" # eip公网
    BAREMETAL = "BAREMETAL" # 裸金属
    CLUSTER = "CLUSTER" # 集群
    CUSTOM_IMAGE = "CUSTOM_IMAGE"   # 自定义镜像
    LOAD_INSTANCE = "LOAD_INSTANCE" # 负载均衡
    GPFS = "GPFS"   # gpfs存储
    OSS = "OSS" # OSS存储
    CEPHFS = "CEPHFS" # cephfs存储
    CONTAINER_IMAGE = "CONTAINER_IMAGE"  # 容器镜像

# 计费方式
class BillingMethod(enum.Enum):
    PostPaid = "PostPaid"   # 按量
    PrePaid = "PrePaid"     # 包年包月

# 计费周期
class BillingCycle(enum.Enum):
    HOUR = "HOUR"
    MONTH = "MONTH"

# 计费状态
class BillingStatus(enum.Enum):
    ACTIVE = "ACTIVE"        # 正常计费
    SUSPENDED = "SUSPENDED"  # 欠费/暂停
    RELEASED = "RELEASED"    # 已释放



