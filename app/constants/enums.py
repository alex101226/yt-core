import enum

# 计费资源type
class ResourceType(enum.Enum):
    SERVER = "SERVER"   # 服务器
    DISK = "DISK"   # 磁盘
    EIP = "EIP" # eip公网
    BAREMETAL = "BAREMETAL" # 裸金属
    CLUSTER = "CLUSTER" # 集群
    AI_STUDIO = "AI_STUDIO"  # AI Studio
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
    HOUR = "HOUR" # 时
    MONTH = "MONTH" # 月

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
    APPROVE = "approve"  # 审批通过
    REJECT = "reject"  # 审批驳回

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

# 模块    'SERVER','EIP','BAREMETAL','CLUSTER','LOAD_INSTANCE','VPC','SUBNET','SECURITY','GPFS','OSS','CEPHFS','CUSTOM_IMAGE','CONTAINER_IMAGE','BILLING','INVOICE','WALLET','REFUND','ORDER','PAYMENT','USER','ROLE','PERMISSION','API_KEY','SYSTEM_CONFIG','SYSTEM_NOTICE','AUDIT_LOG','TASK','SCHEDULE'
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
    CREDIT = "credit"  # 低佣金
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


# ==============================
# 负载均衡实例状态
# ==============================
class LoadBalancerStatus(enum.Enum):
    CREATING = "CREATING"   # 创建中
    RUNNING = "RUNNING"     # 运行中
    STOPPED = "STOPPED"     # 已停止
    UPDATING = "UPDATING"   # 变更中
    DELETING = "DELETING"   # 删除中
    DELETED = "DELETED"     # 已删除
    ERROR = "ERROR"         # 异常


# ==============================
# 负载均衡网络类型
# ==============================
class NetworkType(enum.Enum):
    PUBLIC = "PUBLIC"       # 公网负载均衡
    PRIVATE = "PRIVATE"     # 私网负载均衡


# ==============================
# 负载均衡实例类型
# ==============================
class LBInstanceType(enum.Enum):
    SPEC = "SPEC"  # 按规格
    PAY_AS_YOU_GO = "PAY"  # 按用量（暂不使用）



# ==============================
# 监听器协议
# ==============================
class ListenerProtocol(enum.Enum):
    HTTP = "HTTP"           # HTTP
    HTTPS = "HTTPS"         # HTTPS（需证书）
    TCP = "TCP"             # TCP
    UDP = "UDP"             # UDP


# ==============================
# 监听器状态
# ==============================
class ListenerStatus(enum.Enum):
    CREATING = "CREATING"   # 创建中
    RUNNING = "RUNNING"     # 运行中
    STOPPED = "STOPPED"     # 已停止
    DELETING = "DELETING"   # 删除中
    ERROR = "ERROR"         # 异常


# ==============================
# 后端服务器状态
# ==============================
class BackendStatus(enum.Enum):
    ENABLED = "ENABLED"     # 启用（可转发流量）
    DISABLED = "DISABLED"   # 禁用（不接收流量）
    UNHEALTHY = "UNHEALTHY" # 健康检查失败
    REMOVED = "REMOVED"     # 已移除


# ==============================
# 负载均衡调度算法
# ==============================
class LBAlgorithm(enum.Enum):
    ROUND_ROBIN = "ROUND_ROBIN"     # 轮询
    WEIGHTED_ROUND_ROBIN = "WRR"    # 加权轮询
    LEAST_CONNECTIONS = "LC"        # 最小连接数
    IP_HASH = "IP_HASH"             # 源 IP 哈希



# ==============================
# 健康检查类型
# ==============================
class HealthCheckType(enum.Enum):
    TCP = "TCP"             # TCP 探测
    HTTP = "HTTP"           # HTTP 探测
    HTTPS = "HTTPS"         # HTTPS 探测



# ==============================
# 协议证书证书状态
# ==============================
class LoadCertificateStatus(enum.Enum):
    CREATING = "CREATING"   # 创建中
    AVAILABLE = "AVAILABLE" # 可用
    EXPIRED = "EXPIRED"     # 已过期
    DISABLED = "DISABLED"   # 禁用
    DELETING = "DELETING"   # 删除中
    DELETED = "DELETED"     # 已删除


# ==============================
# 访问控制（ACL）状态
# ==============================
class ACLStatus(enum.Enum):
    ENABLED = "ENABLED"     # 启用
    DISABLED = "DISABLED"   # 禁用
    DELETING = "DELETING"   # 删除中


# ===== 流水方向 =====
class Direction(str, enum.Enum):
    IN = "IN"    # 收入，资金流入账户
    OUT = "OUT"  # 支出，资金流出账户

# ===== 流水类型 =====
class FlowType(str, enum.Enum):
    RECHARGE = "RECHARGE"     # 充值流水
    PAY_ORDER = "PAY_ORDER"   # 消费支付流水（购买商品/服务）
    REFUND = "REFUND"         # 退款（退订或冲正）

# ===== 资金形式 =====
class FundType(str, enum.Enum):
    BALANCE = "BALANCE"   # 用户现金余额
    CREDIT = "CREDIT"     # 平台授信额度（授信/信用）
    VOUCHER = "VOUCHER"   # 代金券 / 优惠券

# ===== 关联业务类型 =====
class RefType(str, enum.Enum):
    RECHARGE_ORDER = "RECHARGE_ORDER"   # 充值单
    PRODUCT_ORDER = "PRODUCT_ORDER"     # 商品订单（一次交易）
    BILLING_DETAIL = "BILLING_DETAIL"   # 账单单据
    REFUND_ORDER = "REFUND_ORDER"       # 退款单

# ===== 渠道 =====
class Channel(str, enum.Enum):
    USER_ACCOUNT = "USER_ACCOUNT"  # 用户账户余额支付
    ALIPAY = "ALIPAY"              # 支付宝支付
    WECHAT = "WECHAT"              # 微信支付
    BANK = "BANK"                  # 银行支付 / 转账
    SYSTEM = "SYSTEM"              # 系统操作或管理员操作

class PayStatus(str, enum.Enum):
    PENDING = "PENDING"  # 待支付
    SUCCESS = "SUCCESS"  # 支付成功
    FAILED = "FAILED"  # 支付失败


class AccountType(enum.Enum):
    PERSONAL = "PERSONAL"
    COMPANY = "COMPANY"

class AccountStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    DELETED = "DELETED"

# 退订资源
class Unsubscribe:
    SERVER = "SERVER" # 服务器
    BAREMETAL = 'BAREMETAL' # 裸金属
    CLUSTER = 'CLUSTER'     # 集群
    GPFS = 'GPFS' # GPFS存储
    CEPHFS = 'CEPHFS'  # CephFS存储
    DISK = "DISK"  # cbs磁盘
    EIP = 'EIP' # 公网IP
    LOAD_INSTANCE = 'LOAD_INSTANCE' # 负载均衡
