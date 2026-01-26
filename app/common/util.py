from datetime import datetime

from app.common.exceptions import BusinessException
from app.common.status_code import ErrorCode


#   生成随机名称，比如订单号之类的
def gen_random_name(name: str):
    return f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

#   文本解析
def parse_acl_rules(source_cidr: str):
    """
    输入：
    192.168.1.1|备注
    10.0.0.0/24|测试
    """

    rules = []
    lines = [line.strip() for line in source_cidr.splitlines() if line.strip()]

    priority = 1
    for line in lines:
        try:
            address, remark = line.split("|", 1)
        except ValueError:
            raise BusinessException(
                code=ErrorCode.FAILED,
                message=f"地址格式错误：{line}"
            )

        address = address.strip()
        remark = remark.strip()

        # 判断 IP / CIDR
        source_type = "CIDR" if "/" in address else "IP"

        rules.append({
            "source_type": source_type,
            "source_value": address,
            "description": remark,
            "priority": priority,
            "action": "ALLOW",  # 默认放行
            "status": "ENABLED",
        })

        priority += 1

    return rules


