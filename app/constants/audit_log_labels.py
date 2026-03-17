from app.constants.enums import ActionMode, ActionOperate


ACTION_MODE_LABELS = {
    ActionMode.SERVER.value: "云服务器",
    ActionMode.DISK.value: "云硬盘",
    ActionMode.EIP.value: "弹性公网",
    ActionMode.BAREMETAL.value: "裸金属",
    ActionMode.CLUSTER.value: "集群",
    ActionMode.LOAD_INSTANCE.value: "负载均衡",
    ActionMode.VPC.value: "VPC",
    ActionMode.SUBNET.value: "子网",
    ActionMode.SECURITY.value: "安全组",
    ActionMode.GPFS.value: "GPFS存储",
    ActionMode.OSS.value: "OSS对象存储",
    ActionMode.CEPHFS.value: "CephFS存储",
    ActionMode.CUSTOM_IMAGE.value: "自定义镜像",
    ActionMode.CONTAINER_IMAGE.value: "容器镜像",
    ActionMode.BILLING.value: "计费",
    ActionMode.INVOICE.value: "发票",
    ActionMode.WALLET.value: "钱包",
    ActionMode.CREDIT.value: "低佣金",
    ActionMode.REFUND.value: "退款",
    ActionMode.ORDER.value: "订单",
    ActionMode.PAYMENT.value: "支付",
    ActionMode.USER.value: "用户",
    ActionMode.ROLE.value: "角色",
    ActionMode.PERMISSION.value: "权限",
    ActionMode.API_KEY.value: "访问密钥",
    ActionMode.SYSTEM_CONFIG.value: "系统配置",
    ActionMode.SYSTEM_NOTICE.value: "系统通知",
    ActionMode.AUDIT_LOG.value: "审计日志",
    ActionMode.TASK.value: "任务",
    ActionMode.SCHEDULE.value: "调度",
}


ACTION_OPERATE_LABELS = {
    ActionOperate.CREATE.value: "创建",
    ActionOperate.UPDATE.value: "更新",
    ActionOperate.RELEASE.value: "删除",
    ActionOperate.APPROVE.value: "审批通过",
    ActionOperate.REJECT.value: "审批驳回",
    ActionOperate.START.value: "启动",
    ActionOperate.STOP.value: "停止",
    ActionOperate.REBOOT.value: "重启",
    ActionOperate.CREATE_IMAGE.value: "创建镜像",
    ActionOperate.CHANGE_IMAGE.value: "更换镜像",
    ActionOperate.CLONE.value: "克隆",
    ActionOperate.ENABLE_SSH_PROXY.value: "开启SSH代理",
    ActionOperate.DISABLE_SSH_PROXY.value: "关闭SSH代理",
    ActionOperate.RESET_PASSWORD.value: "重置密码",
    ActionOperate.CHANGE_CHARGE_TYPE.value: "变更计费方式",
    ActionOperate.EXPAND.value: "扩容",
    ActionOperate.DISABLE_RELEASE_PROTECT.value: "关闭释放保护",
    ActionOperate.BIND.value: "绑定",
    ActionOperate.UNBIND.value: "解绑",
}


def get_action_mode_label(value: str) -> str:
    return ACTION_MODE_LABELS.get(value, value)


def get_action_operate_label(value: str) -> str:
    return ACTION_OPERATE_LABELS.get(value, value)
