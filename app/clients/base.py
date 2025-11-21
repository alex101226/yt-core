from typing import List, Dict, Optional


class BaseCloudClient:
    """统一云客户端接口"""

    def list_regions(self) -> List[Dict]:
        raise NotImplementedError

    def list_zones(self, region_id: str) -> List[Dict]:
        raise NotImplementedError

    def list_vpcs(self, region_id: str) -> List[Dict]:
        raise NotImplementedError

    def list_vswitches(self, region_id: str, vpc_id: str) -> List[Dict]:
        raise NotImplementedError

    def list_security_groups(self, region_id: Optional[str] = None, vpc_id: Optional[str] = None, page: int = 1, page_size: int = 50):
        raise NotImplementedError

    def list_security_group_rules(self, region_id: str, security_group_id: str):
        raise NotImplementedError

    def list_images(self, region_id: Optional[str] = None) -> List[dict]:
        raise NotImplementedError

    def list_instance_types(self, region_id: str) -> List[dict]:
        raise NotImplementedError

    def list_pricing_options(self) -> List[dict]:
        raise NotImplementedError