import ipaddress

# ip计算
def allocate_private_ip(cidr, used_ips):
    net = ipaddress.ip_network(cidr)

    for ip in net.hosts():  # hosts() 自动跳过网络号和广播地址
        if str(ip) not in used_ips:
            return str(ip)

    raise Exception("No available IP in this subnet")
