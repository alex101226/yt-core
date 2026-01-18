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

# 操作动作
class ActionOperate(enum.Enum):
    # ========== 基础 CRUD ==========
    CREATE = "create"  # 创建
    UPDATE = "update"  # 更新
    RELEASE = "release"  # 删除 / 释放

    # ========== 实例生命周期 ==========
    START = "start"  # 开机
    STOP = "stop"  # 关机
    REBOOT = "reboot"  # 重启

    # ========== 镜像相关 ==========
    CREATE_IMAGE = "create_image"  # 创建镜像
    CHANGE_IMAGE = "change_image"  # 更换镜像
    CLONE = "clone"  # 克隆实例

    # ========== 网络 / 访问 ==========
    ENABLE_SSH_PROXY = "enable_ssh_proxy"  # 开启 SSH 代理
    DISABLE_SSH_PROXY = "disable_ssh_proxy"  # 关闭 SSH 代理

    # ========== 安全 / 密码 ==========
    RESET_PASSWORD = "reset_password"  # 修改管理密码

    # ========== 计费相关 ==========
    CHANGE_CHARGE_TYPE = "change_charge_type"

    # ========== 资源配置 ==========
    EXPAND = "expand"  # 扩容（CPU / 内存 / 磁盘）

    # ========== 保护 / 策略 ==========
    DISABLE_RELEASE_PROTECT = "disable_release_protect"  # 关闭释放保护

    # ========== 资源绑定关系 ==========
    BIND = "bind"  # 绑定（如 EIP 绑定实例、磁盘挂载）
    UNBIND = "unbind"  # 解绑

# 模块
class ActionMode(enum.Enum):
    # ========== 计算 / 资源 ==========
    SERVER = "server"  # 云服务器
    DISK = "disk"  # 磁盘
    EIP = "eip"  # 公网 EIP
    BAREMETAL = "baremetal"  # 裸金属
    CLUSTER = "cluster"  # 集群
    LOAD_INSTANCE = "load_instance"  # 负载均衡
    VPC = "vpc"
    SUBNET = "subnet"
    SECURITY = "security"

    # ========== 存储 ==========
    GPFS = "gpfs"  # GPFS 存储
    OSS = "oss"  # 对象存储
    CEPHFS = "cephfs"  # CEPHFS 存储

    # ========== 镜像 ==========
    CUSTOM_IMAGE = "custom_image"  # 自定义镜像
    CONTAINER_IMAGE = "container_image"  # 容器镜像

    # ========== 计费 / 财务 ==========
    BILLING = "billing"  # 计费（扣费、账单）
    INVOICE = "invoice"  # 发票
    WALLET = "wallet"  # 钱包 / 余额
    REFUND = "refund"  # 退款

    # ========== 订单 / 交易 ==========
    ORDER = "order"  # 订单
    PAYMENT = "payment"  # 支付

    # ========== 账号 / 权限 ==========
    USER = "user"  # 用户
    ROLE = "role"  # 角色
    PERMISSION = "permission"  # 权限
    API_KEY = "api_key"  # API Key / 访问密钥

    # ========== 系统 / 平台 ==========
    SYSTEM_CONFIG = "system_config"  # 系统配置
    SYSTEM_NOTICE = "system_notice"  # 系统通知
    AUDIT_LOG = "audit_log"  # 审计日志本身

    # ========== 运维 / 管理 ==========
    TASK = "task"  # 异步任务 / 工单
    SCHEDULE = "schedule"  # 定时任务