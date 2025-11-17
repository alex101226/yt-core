# app/clients/aliyun_client.py
from typing import List
from alibabacloud_ecs20140526.client import Client as EcsClient
from alibabacloud_ecs20140526 import models as ecs_models
from app.common.credentials_manager import CredentialsManager


class AliyunClient:
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

    # --------------------------
    # ECS 镜像
    # --------------------------
    def list_images(self, region_id: str, os_type: str = "linux") -> List[dict]:
        """
        获取指定 Region 的 ECS 镜像列表
        :param region_id: 云区域 ID
        :param os_type: 系统类型，可选 "linux" 或 "windows"
        :return: 镜像列表，每个字典包含 image_id, image_name, os_type
        """
        request = ecs_models.DescribeImagesRequest(region_id=region_id, os_type=os_type)
        response = self.client.describe_images(request)
        return [
            {"image_id": i.image_id, "image_name": i.image_name, "os_type": i.os_type}
            for i in response.body.images.image
        ]

    # --------------------------
    # 实例规格（实例类型）
    # --------------------------
    def list_instance_types(self, region_id: str) -> List[dict]:
        """
        获取指定 Region 的实例规格列表
        :param region_id: 云区域 ID
        :return: 实例规格列表，每个字典包含 instance_type, cpu, memory
        """
        request = ecs_models.DescribeInstanceTypesRequest(region_id=region_id)
        response = self.client.describe_instance_types(request)
        return [
            {
                "instance_type": t.instance_type,
                "cpu": t.cpu,
                "memory": t.memory,
            }
            for t in response.body.instance_types.instance_type
        ]

    # --------------------------
    # 计费方式
    # --------------------------
    def list_pricing_options(self) -> List[dict]:
            """
            获取 ECS 可选计费方式
            注意：阿里云 ECS 计费方式通常固定为按量付费或包年包月，可根据需求在前端做映射
            :return: 计费方式列表，每个字典包含 code, name
            """
            # 这里我们返回静态列表，前端可选择
            return [
                {"code": "PayAsYouGo", "name": "按量付费"},
                {"code": "PrePaid", "name": "包年包月"}
            ]


class AliyunClientFactory:
    """阿里云客户端工厂"""

    @staticmethod
    def create_client(access_key_id: str, access_key_secret: str, endpoint: str = "ecs.aliyuncs.com") -> AliyunClient:
        return AliyunClient(access_key_id, access_key_secret, endpoint)
