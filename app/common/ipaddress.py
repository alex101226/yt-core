import ipaddress
import random

# ip计算
def allocate_private_ip(cidr, used_ips):
    net = ipaddress.ip_network(cidr)

    for ip in net.hosts():  # hosts() 自动跳过网络号和广播地址
        if str(ip) not in used_ips:
            return str(ip)

    raise Exception("No available IP in this subnet")


# 区域映射ip
def region_map_ip(region: str) -> str:
    if region.startswith("cn-"):
        return "203.0.113.0/24"

        # 兜底（如果以后有别的区域）
    return "198.51.100.0/24"

# 根据区域生成公网ip
def create_public_ip(region: str) -> str:
    cidr = region_map_ip(region)
    network = ipaddress.ip_network(cidr)

    # 排除 network / broadcast
    usable_ips = list(network.hosts())

    return str(random.choice(usable_ips))
