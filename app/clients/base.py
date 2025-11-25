from typing import List, Dict, Optional


class BaseCloudClient:
    """统一云客户端接口"""
    # 获取区域
    def list_regions(self) -> List[Dict]:
        raise NotImplementedError
    # 获取可用区
    def list_zones(self, region_id: str) -> List[Dict]:
        raise NotImplementedError

    # 获取vpc
    def list_vpcs(self, region_id: str) -> List[Dict]:
        raise NotImplementedError

    # 获取子网
    def list_vswitches(self, region_id: str, vpc_id: str) -> List[Dict]:
        raise NotImplementedError

    # 获取安全组
    def list_security_groups(self, region_id: Optional[str] = None, vpc_id: Optional[str] = None, page: int = 1, page_size: int = 50):
        raise NotImplementedError

    # 获取安全组配置
    def list_security_group_rules(self, region_id: str, security_group_id: str):
        raise NotImplementedError

    # 获取系统镜像
    def list_images(self, region_id: Optional[str] = None) -> List[dict]:
        raise NotImplementedError

    # 获取全量规格
    def list_instance_types(self, provider_code: str, region_id: str, min_cpu: int = 1, min_memory: int = 1, architecture: str = "x86_64", bare_metal: bool = False) -> List[dict]:
        raise NotImplementedError

    # 获取可用区规格
    def list_available_instance_types(
        self,
        region_id: str = None,
        zone_id: str = None,
        include_soldout: bool = False) -> List[dict]:
        raise NotImplementedError

    # 获取价格
    def list_pricing_options(
        self,
        region_id: str,
        instance_type: str,
        charge_type: str = "PostPaid",
        period: int = 1,
    ) -> List[dict]:
        raise NotImplementedError