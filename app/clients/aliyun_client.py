# app/clients/aliyun_client.py
from typing import List, Optional, Any
import re

from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from app.common.credentials_manager import CredentialsManager
from app.clients.base import BaseCloudClient

from app.core.logger import logger

SYSTEM_DISK_TYPES = [
    "cloud_auto",
    "cloud_essd",
    "cloud_efficiency",
    "cloud_ssd",
    "cloud_essd_entry",
    "cloud",
    "ephemeral_ssd",
]

def _get_attr_any(obj: Any, *names: str):
    """
    尝试按多个候选属性名获取属性值（兼容多种命名风格）。
    支持：
      - 直接属性名（obj.foo）
      - 大驼峰/小驼峰/下划线（InstanceTypeId / instanceTypeId / instance_type_id）
      - dict 访问（obj.get(key)）
    返回第一个存在且不为 None 的值，否则返回 None。
    """
    if obj is None:
        return None

    # 如果对象是 dict-like
    if isinstance(obj, dict):
        for n in names:
            if n in obj and obj[n] is not None:
                return obj[n]

    # 普通对象，尝试属性访问
    for n in names:
        if hasattr(obj, n):
            val = getattr(obj, n)
            if val is not None:
                return val

    # 补尝试常见变形： CamelCase, lowerCamel, snake_case
    def variants(base: str):
        # base may be e.g. instance_type_id or InstanceTypeId
        yield base
        # snake -> CamelCase
        s = base
        if "_" in s:
            parts = s.split("_")
            yield "".join(p.capitalize() for p in parts)         # InstanceTypeId
            yield parts[0] + "".join(p.capitalize() for p in parts[1:])  # instanceTypeId
        else:
            # Camel -> snake
            # convert CamelCase to snake_case
            snake = re.sub('([A-Z]+)', r'_\1', s).lower().lstrip("_")
            if snake != s:
                yield snake
                yield snake.capitalize()
                yield snake.split("_")[0] + "".join(p.capitalize() for p in snake.split("_")[1:])

    for base in names:
        for v in variants(base):
            if hasattr(obj, v):
                val = getattr(obj, v)
                if val is not None:
                    return val
            if isinstance(obj, dict) and v in obj and obj[v] is not None:
                return obj[v]

    return None


def _extract_items_from_response(response) -> List[Any]:
    """
    兼容各种可能的返回路径，返回实例规格对象列表（原始 SDK 对象或 dict）。
    常见路径：
      - response.body.instance_types.instance_type
      - response.instance_types.instance_type
      - response.instance_types
      - response.get('InstanceTypes')
    """
    # 1) 尝试常见 SDK 属性链
    try:
        # 有些 SDK 把 body 放在 response.body
        body = getattr(response, "body", response)
        # 常见嵌套： instance_types.instance_type
        itypes = None
        if hasattr(body, "instance_types"):
            itypes_container = getattr(body, "instance_types")
            # container 里可能有 instance_type 属性（list）
            if hasattr(itypes_container, "instance_type"):
                itypes = getattr(itypes_container, "instance_type")
            else:
                # 可能就是列表或 dict
                itypes = itypes_container
        # 有些 SDK 直接把 InstanceTypes 放为 dict/list
        if itypes is None:
            # try dictionary style
            if isinstance(body, dict):
                itypes = body.get("InstanceTypes") or body.get("instance_types")
            else:
                # fallback: try top-level instance_types
                itypes = getattr(body, "InstanceTypes", None) or getattr(body, "instance_types", None)

        # normalize: if itypes is a single object, wrap into list
        if itypes is None:
            return []
        if not isinstance(itypes, list):
            # sometimes it's an object with attribute instance_type
            if hasattr(itypes, "instance_type"):
                maybe = getattr(itypes, "instance_type")
                return maybe if isinstance(maybe, list) else [maybe]
            return [itypes]

        return itypes

    except Exception:
        # 最后兜底：把 response 转 dict（若 SDK 提供）或打印
        try:
            # 如果 SDK 对象有 to_map / to_dict 方法
            if hasattr(response, "to_map"):
                m = response.to_map()
                # 尝试常见 key
                if "InstanceTypes" in m:
                    it = m["InstanceTypes"]
                    if isinstance(it, dict) and "InstanceType" in it:
                        return it["InstanceType"]
                    return it
            if hasattr(response, "to_dict"):
                m = response.to_dict()
                return m.get("InstanceTypes") or m.get("instance_types") or []
        except Exception:
            pass
    return []

class AliyunClient(BaseCloudClient):
    """阿里云 ECS 客户端封装"""

    def __init__(self, access_key_id: str, access_key_secret: str, endpoint: str = "ecs.aliyuncs.com"):
        cred_client = CredentialsManager.build_aliyun_client(access_key_id, access_key_secret)
        config = CredentialsManager.build_aliyun_product_config(cred_client, endpoint)
        self.client = EcsClient(config)

    # --------------------------
    # 区域
    # --------------------------
    def list_regions(self) -> List[dict]:
        """获取阿里云区域列表"""
        request = ecs_models.DescribeRegionsRequest()
        response = self.client.describe_regions(request)
        return [
            {"region_id": r.region_id, "region_name": r.local_name}
            for r in response.body.regions.region
        ]

    # --------------------------
    # 可用区
    # --------------------------
    def list_zones(self, region_id: str) -> List[dict]:
        request = ecs_models.DescribeZonesRequest(region_id=region_id)
        response = self.client.describe_zones(request)
        return [
            {"zone_id": z.zone_id, "zone_name": z.local_name}
            for z in response.body.zones.zone
        ]


    # --------------------------
    # 获取指定 Region 下的 VPC 列表
    # --------------------------
    def list_vpcs(self, region_id: str) -> List[dict]:
        """
        获取指定 Region 下的 VPC 列表
        :param region_id: 云区域 ID
        :return: VPC 列表，每个 VPC 字典包含 vpc_id、vpc_name、cidr_block 等
        """
        request = ecs_models.DescribeVpcsRequest(region_id=region_id)
        response = self.client.describe_vpcs(request)
        return [
            {
                "vpc_id": v.vpc_id,
                "vpc_name": v.vpc_name,
                "cidr_block": v.cidr_block,
                "is_default": v.is_default,
            }
            for v in response.body.vpcs.vpc
        ]

    # --------------------------
    # 获取指定 VPC 下的子网列表
    # --------------------------
    def list_vswitches(self, region_id: str, vpc_id: str) -> List[dict]:
        """
        获取指定 VPC 下的子网列表
        :param region_id: 云区域 ID
        :param vpc_id: VPC ID
        :return: 子网列表，每个字典包含 vswitch_id、vswitch_name、cidr_block、zone_id
        """
        request = ecs_models.DescribeVSwitchesRequest(region_id=region_id, vpc_id=vpc_id)
        response = self.client.describe_vswitches(request)
        vswitch_list = getattr(response.body.vswitches, "vswitch", []) or []
        return [
            {
                "vswitch_id": v.vswitch_id,
                "vswitch_name": v.vswitch_name,
                "cidr_block": v.cidr_block,
                "zone_id": v.zone_id,
            }
            for v in vswitch_list
        ]

    # -----------------------------------------------------------
    # 获取安全组列表（分页）
    # -----------------------------------------------------------
    def list_security_groups(self, region_id: Optional[str] = None, vpc_id: Optional[str] = None, page: int = 1, page_size: int = 50):
        # ---- 正确：构建阿里云 Request 对象 ----
        req = ecs_models.DescribeSecurityGroupsRequest(
            region_id=region_id,
            vpc_id=vpc_id,
            page_number=page,
            page_size=page_size,
        )
        # ---- 正确：不再传 dict ----
        resp = self.client.describe_security_groups(req)

        # ---- 阿里云返回是 TeaModel，应转成 dict ----
        resp_dict = resp.to_map() if hasattr(resp, "to_map") else resp

        items = []
        total = 0

        try:
            # 适配阿里云 ECS 返回结构
            gs = (
                resp_dict.get("body", {})
                .get("SecurityGroups", {})
                .get("SecurityGroup", [])
            )

            total = (
                resp_dict.get("body", {}).get("TotalCount", len(gs))
            )

            for g in gs:
                items.append({
                    "SecurityGroupId": g.get("SecurityGroupId"),
                    "SecurityGroupName": g.get("SecurityGroupName"),
                    "Description": g.get("Description"),
                    "VpcId": g.get("VpcId"),
                    "ResourceGroupId": g.get("ResourceGroupId"),
                })

        except Exception as e:
            print("Parse SecurityGroup Error:", e)

        return {"total": total, "items": items}


    # --------------------------
    # 获取安全组的入方向+出方向规则
    # --------------------------
    def list_security_group_rules(self, region_id: str, security_group_id: str):
        req = ecs_models.DescribeSecurityGroupAttributeRequest(
            region_id=region_id,
            security_group_id=security_group_id
        )
        resp = self.client.describe_security_group_attribute(req)
        perms = resp.body.permissions.permission or []

        rules = []
        for p in perms:
            rules.append({
                "direction": p.direction,                  # inbound / outbound
                "protocol_code": p.ip_protocol,            # TCP/UDP/ALL
                "port_range": p.port_range,                # 80/80
                "policy_code": p.policy,                   # accept/ drop
                "source": p.source_cidr_ip or p.dest_cidr_ip,  # 可能在 Source 或 Dest
                "description": p.description,
                "cloud_rule_id": p.security_group_rule_id,
            })

        return rules

    # --------------------------
    # ECS 镜像
    # --------------------------
    def list_images(self, region_id: Optional[str] = None) -> List[dict]:
        request = ecs_models.DescribeImagesRequest(region_id=region_id, image_owner_alias="system")
        response = self.client.describe_images(request)
        images = response.body.images.image or []
        return [
            {
                "image_id": i.image_id,
                "image_name": i.image_name,
            }
            for i in images
        ]

    # --------------------------
    # 实例规格（实例类型）     region_id: str, min_cpu: int = 1, min_memory: int = 1, architecture: str = "x86_64", bare_metal: bool = False
    # --------------------------
    def list_instance_types(self, provider_code: str, region_id: Optional[str] = None, min_cpu: int = 1, min_memory: int = 1, architecture: str = "x86_64", bare_metal: bool = False) -> List[dict]:
        # -------------------------------
        # 1. 调用 DescribeInstanceTypes 获取全量规格详情
        # -------------------------------
        request = ecs_models.DescribeInstanceTypesRequest()
        response = self.client.describe_instance_types(request)

        items = response.body.instance_types.instance_type  # list

        # 如果 items 为空，打印调试信息（可删除）
        if not items:
            # 帮助定位 SDK 返回结构
            try:
                print("DEBUG: response attrs:", dir(response)[:200])
                if hasattr(response, "body"):
                    print("DEBUG: body attrs:", dir(response.body)[:200])
                    if hasattr(response.body, "instance_types"):
                        print("DEBUG: instance_types attrs:", dir(response.body.instance_types)[:200])
                # 如果有 to_map/to_dict，打印 keys
                if hasattr(response, "to_map"):
                    print("DEBUG: response.to_map() keys:", list(response.to_map().keys()))
                if hasattr(response, "to_dict"):
                    print("DEBUG: response.to_dict() keys:", list(response.to_dict().keys()))
            except Exception as e:
                print("DEBUG: failed to inspect response:", e)

            return []

        results: List[dict] = []
        for it in items:
            # 下面用 _get_attr_any 去兼容不同命名方式
            it_id = _get_attr_any(it, "InstanceTypeId", "instance_type_id", "instanceTypeId")
            instance_family = _get_attr_any(it, "InstanceTypeFamily", "instance_family", "instanceFamily")
            # 代次尝试从 instance_family 提取，例如 ecs.g7 -> g7
            generation = None
            if instance_family:
                try:
                    # instance_family 可能是 'ecs.g7' 或 'g7'
                    if "." in instance_family:
                        generation = instance_family.split(".")[-1]
                    else:
                        generation = instance_family
                except Exception:
                    generation = None

            cpu = _get_attr_any(it, "CpuCoreCount", "cpu_core_count", "cpuCount", "vcpu")
            mem = _get_attr_any(it, "MemorySize", "memory_size", "memory")
            arch = _get_attr_any(it, "CpuArchitecture", "cpu_architecture", "architecture")

            gpu_amount = _get_attr_any(it, "GPUAmount", "gpu_amount", "gpuAmount")
            gpu_spec = _get_attr_any(it, "GPUSpec", "gpu_spec", "gpuSpec")
            gpu_mem = _get_attr_any(it, "GPUMemory", "gpu_memory", "gpuMemory")

            local_amount = _get_attr_any(it, "LocalStorageAmount", "local_storage_amount")
            local_capacity = _get_attr_any(it, "LocalStorageCapacity", "local_storage_capacity")

            network_perf = _get_attr_any(it, "NetworkInfo", "NetworkPerformance", "network_performance",
                                         "networkPerformance")
            # 如果 network_perf 是复杂对象，需要序列化成字符串
            if network_perf and not isinstance(network_perf, (str, int, float)):
                try:
                    # 如果它是 SDK 对象，尝试 to_map / to_dict
                    if hasattr(network_perf, "to_map"):
                        network_perf = str(network_perf.to_map())
                    elif hasattr(network_perf, "to_dict"):
                        network_perf = str(network_perf.to_dict())
                    else:
                        network_perf = str(network_perf)
                except Exception:
                    network_perf = str(network_perf)

            # 过滤条件：最低 cpu / memory / architecture / bare_metal（示例）
            try:
                if cpu is None:
                    cpu_val = 0
                else:
                    cpu_val = int(cpu)
            except Exception:
                cpu_val = 0

            try:
                mem_val = float(mem) if mem is not None else 0.0
            except Exception:
                mem_val = 0.0

            if cpu_val < min_cpu:
                continue
            if mem_val < min_memory:
                continue
            # architecture 简单匹配（x86_64 -> x86）
            if architecture and arch:
                if architecture.lower().startswith("x86") and not str(arch).lower().startswith("x86"):
                    continue
                if architecture.lower().startswith("arm") and not str(arch).lower().startswith("arm"):
                    continue
            # bare_metal 判断：根据 instance_family 或 generation 中是否包含 'ebm' / 'bare' 等关键字
            if bare_metal:
                fam = (instance_family or "").lower()
                gen = (generation or "").lower()
                if ("ebm" not in fam) and ("bare" not in fam) and ("ebm" not in gen) and ("bare" not in gen):
                    continue

            results.append({
                "instance_type_id": it_id,
                "instance_family": instance_family,
                "generation": generation,
                "cpu_core_count": cpu_val,
                "memory_size": mem_val,
                "architecture": arch,
                "gpu_amount": int(gpu_amount) if gpu_amount is not None else 0,
                "gpu_spec": gpu_spec,
                "gpu_memory": float(gpu_mem) if gpu_mem is not None else None,
                "local_storage_amount": int(local_amount) if local_amount is not None else None,
                "local_storage_capacity": int(local_capacity) if local_capacity is not None else None,
                "network_performance": network_perf,
                "is_io_optimized": True,
                "price": None,
                "cloud_provider_code": provider_code
            })

        return results

    # --------------------------
    # 可用区     region_id: str, min_cpu: int = 1, min_memory: int = 1, architecture: str = "x86_64", bare_metal: bool = False
    # --------------------------
    def list_available_instance_types(
            self,
            region_id: str = None,
            zone_id: str = None,
            include_soldout: bool = False):
        request = ecs_models.DescribeAvailableResourceRequest(
            region_id=region_id,
            zone_id=zone_id,
            destination_resource="InstanceType"
            # IoOptimized=None, # 可选
        )
        available_types = []

        response = self.client.describe_available_resource(request)
        body = response.body

        if body:
            available_zones = body.available_zones.available_zone

            # 遍历可用区列表
            if not isinstance(available_zones, list):
                available_zones = [available_zones]

            for az in available_zones:
                az_id = az.zone_id
                resources = az.available_resources.available_resource
                if not isinstance(resources, list):
                    resources = [resources]

                for resource in resources:
                    if resource.type != "InstanceType":
                        continue

                    supported_resources = resource.supported_resources.supported_resource
                    if not isinstance(supported_resources, list):
                        supported_resources = [supported_resources]

                    for inst in supported_resources:
                        if inst.status == "SoldOut":
                            continue
                        # 只要有库存或 include_soldout 为 True
                        if not include_soldout and inst.status_category != "WithStock":
                            continue
                        available_types.append({
                            "instance_type_id": inst.value,
                            "status": inst.status,
                            "status_category": inst.status_category,
                            "zone_id": az_id,
                            "max_available": getattr(inst, "max", None),
                            "unit": getattr(inst, "unit", None),
                            # "system_disk_category": system_disk_category
                        })

        return available_types

    # --------------------------
    # 获取 ECS 可选计费方式
    # --------------------------
    def list_pricing_options(
        self,
        region_id: str,
        instance_type: str,
        charge_type: str = "PostPaid",
        period: int = 1,
    ):
        for disk_type in SYSTEM_DISK_TYPES:
            req = ecs_models.DescribePriceRequest(
                region_id=region_id,
                instance_type=instance_type,
                # resource_type="instance"
            )

            if charge_type == "PostPaid":  # 按量
                req.price_unit = "Hour"
            elif charge_type == "PrePaid":  # 包年包月
                req.price_unit = "Month"
                req.period = period
                req.period_unit = "Month"
            elif charge_type == "Spot":  # 抢占式
                req.price_unit = "Hour"
                req.spot_strategy = "SpotAsPriceGo"
            req.system_disk_category = disk_type
            try:
                resp = self.client.describe_price(req)
                # logger.info(f'看下这个 {resp}')

                detail_infos = resp.body.price_info.price.detail_infos.detail_info
                # logger.info(f'再次看价格！！！！11 {resp.body.price_info.price.trade_price}')

                # logger.info(f'查看价格 {detail_infos}')
                # 只取实例 + 系统盘价格
                prices = {item.resource: item.trade_price for item in detail_infos}
                normalized = {k.lower(): v for k, v in prices.items()}
                return normalized
            except Exception as ex:
                # 如果是 invalid category → 换下一个
                msg = str(ex)
                if "InvalidSystemDiskCategory.ValueNotSupported" in msg:
                    continue
                # 如果是其他错误，就直接抛出
                raise ex
             # 所有类型都失败
        return {
            "instancetype": 0,
            "systemdisk": 0
        }

class AliyunClientFactory:
    """阿里云客户端工厂"""

    @staticmethod
    def create_client(access_key_id: str, access_key_secret: str, endpoint: str = "ecs.aliyuncs.com") -> AliyunClient:
        return AliyunClient(access_key_id, access_key_secret, endpoint)
