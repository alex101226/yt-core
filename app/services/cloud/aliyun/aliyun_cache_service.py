from app.common.cache_util import cache_get, cache_set, cache_delete
from app.services.cloud.aliyun.aliyun_cache_keys import (
    ALIYUN_REGION_KEY,
    aliyun_zones_key,
    aliyun_images_key,
    aliyun_instance_types_key,
    aliyun_available_types_key,
    aliyun_system_disks_key,
    aliyun_cloud_price_key,
)

class AliyunCacheService:

    # 1）区域缓存
    async def get_regions(self):
        return await cache_get(ALIYUN_REGION_KEY)

    async def set_regions(self, data):
        return await cache_set(ALIYUN_REGION_KEY, data)

    # 2）可用区
    async def get_zones(self, region_id: str):
        return await cache_get(aliyun_zones_key(region_id))

    async def set_zones(self, region_id: str, data):
        return await cache_set(aliyun_zones_key(region_id), data)

    # 3）镜像
    async def get_images(self, region_id: str):
        return await cache_get(aliyun_images_key(region_id))

    async def set_images(self, region_id: str, data):
        return await cache_set(aliyun_images_key(region_id), data)

    # 4）全量实例规格
    async def get_instance_types(self, region_id: str):
        return await cache_get(aliyun_instance_types_key(region_id))

    async def set_instance_types(self, region_id: str, data):
        return await cache_set(aliyun_instance_types_key(region_id), data)

    async def del_instance_types(self, region_id: str):
        return await cache_delete(aliyun_instance_types_key(region_id))
    # 可用区实例规格
    async def get_available_types(self, region_id: str):
        return await cache_get(aliyun_available_types_key(region_id))

    async def set_available_types(self, region_id: str, data):
        return await cache_set(aliyun_available_types_key(region_id), data)

    async def del_available_types(self, region_id: str):
        return await cache_delete(aliyun_available_types_key(region_id))

    # 5）磁盘
    async def get_system_disks(self, region_id: str):
        return await cache_get(aliyun_system_disks_key(region_id))

    async def set_system_disks(self, region_id: str, data):
        return await cache_set(aliyun_system_disks_key(region_id), data)

    # 6）价格
    async def get_cloud_prices(self, region_id: str):
        return await cache_get(aliyun_cloud_price_key(region_id))

    async def set_cloud_prices(self, region_id: str, data):
        return await cache_set(aliyun_cloud_price_key(region_id), data)
