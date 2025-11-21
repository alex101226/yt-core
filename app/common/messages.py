# app/common/messages.py

class Message:
    # === 通用 ===
    SUCCESS = "操作成功"
    FAILED = "操作失败"
    PARAMS_ERROR="参数校验失败"

    # === 用户相关 ===
    USER_NOT_FOUND = "用户不存在"
    USER_ALREADY_EXISTS = "用户已存在"
    LOGIN_FAILED = "登录失败，用户名或密码错误"
    PERMISSION_DENIED = "权限不足"

    # === 云厂商相关 ===
    CLOUD_PROVIDER_EXISTS = "云厂商编码已存在"
    CLOUD_PROVIDER_NOT_FOUND = "云厂商不存在"
    CLOUD_PROVIDER_UPDATE_FAILED = "云厂商更新失败"
    CLOUD_PROVIDER_DELETE_FAILED = "云厂商删除失败"

    # === 资源组相关 ===
    RESOURCE_GROUP_NOT_FOUND = "资源组不存在"
    RESOURCE_GROUP_EXISTS = "资源组已存在"
    RESOURCE_GROUP_DELETE_FAILED = "资源组删除失败"

    # === 资源绑定相关 ===
    RESOURCE_ALREADY_BOUND = "该资源已绑定其他资源组"
    RESOURCE_BINDING_NOT_FOUND = "资源绑定不存在"
    RESOURCE_BINDING_FAILED = "资源绑定失败"
    RESOURCE_UNBIND_FAILED = "解除绑定失败"

    # === 数据相关 ===
    DATA_NOT_FOUND = "数据未找到"
    DATA_INVALID = "数据不合法"
    DATA_DUPLICATE = "数据已存在"

    # === 系统相关 ===
    SERVER_ERROR = "服务器内部错误"
    DATABASE_ERROR = "数据库操作失败"
    TIMEOUT_ERROR = "请求超时"
