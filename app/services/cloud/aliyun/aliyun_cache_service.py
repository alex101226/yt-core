from app.common.cache_util import cache_get, cache_set, cache_delete
from app.services.cloud.aliyun.aliyun_cache_keys import (
    cloud_regions_key,
    cloud_zones_key,
    cloud_images_key,
    cloud_instance_types_key,
    cloud_available_types_key,
    cloud_system_disks_key,
    cloud_prices_key,
)

class AliyunCacheService:

    # 1）区域缓存
    async def get_regions(self, cloud_code: str):
        return await cache_get(cloud_regions_key(cloud_code))

    async def set_regions(self, cloud_code: str, data):
        return await cache_set(cloud_regions_key(cloud_code), data)

    # 2）可用区
    async def get_zones(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_zones_key(cloud_code, region_id))

    async def set_zones(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_zones_key(cloud_code, region_id), data)

    # 3）镜像
    async def get_images(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_images_key(cloud_code, region_id))

    async def set_images(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_images_key(cloud_code, region_id), data)

    # 4）全量实例规格
    async def get_instance_types(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_instance_types_key(cloud_code, region_id))

    async def set_instance_types(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_instance_types_key(cloud_code, region_id), data)

    async def del_instance_types(self, cloud_code: str, region_id: str):
        return await cache_delete(cloud_instance_types_key(cloud_code, region_id))
    # 可用区实例规格
    async def get_available_types(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_available_types_key(cloud_code, region_id))

    async def set_available_types(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_available_types_key(cloud_code, region_id), data)

    async def del_available_types(self, cloud_code: str, region_id: str):
        return await cache_delete(cloud_available_types_key(cloud_code, region_id))

    # 5）磁盘
    async def get_system_disks(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_system_disks_key(cloud_code, region_id))

    async def set_system_disks(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_system_disks_key(cloud_code, region_id), data)

    # 6）价格
    async def get_cloud_prices(self, cloud_code: str, region_id: str):
        return await cache_get(cloud_prices_key(cloud_code, region_id))

    async def set_cloud_prices(self, cloud_code: str, region_id: str, data):
        return await cache_set(cloud_prices_key(cloud_code, region_id), data)
