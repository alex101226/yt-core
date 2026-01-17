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
    CREATED = "CREATED"  # 已创建，未完成首单
    ACTIVE = "ACTIVE"        # 正常计费
    SUSPENDED = "SUSPENDED"  # 欠费/暂停
    RELEASED = "RELEASED"    # 已释放


# 发票状态枚举
class InvoiceItemStatus(enum.Enum):
    UNISSUED = "unissued"   # 未开票
    ISSUED = "issued"       # 已开票

# 发票记录类型枚举
class InvoiceRecordType(enum.Enum):
    GENERAL = "general"      # 增值税普通发票
    SPECIAL = "special"      # 增值税专用发票

# 发票记录状态枚举
class InvoiceRecordStatus(enum.Enum):
    ISSUED = "issued"        # 已开票
    CANCELLED = "cancelled"  # 作废

# 云服务器自定义系统镜像状态
class CloudImageStatus(enum.Enum):
    AVAILABLE = "available" # 可用
    DISABLED = "disabled"   # 禁用
    DELETED = "deleted"     # 删除
