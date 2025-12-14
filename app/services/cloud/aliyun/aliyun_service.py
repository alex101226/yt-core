from app.services.cloud.aliyun.aliyun_cache_service import AliyunCacheService
# from app.clients.aliyun_client import AliyunClient
from app.clients.cloud_client_factory import CloudClientFactory

from app.core.logger import logger

class AliyunService:
    def __init__(self, access_key_id: str, access_key_secret: str):
        self.cache = AliyunCacheService()
        self.client = CloudClientFactory.create_client(
            "aliyun", access_key_id, access_key_secret, 'ecs.aliyuncs.com'
        )

    # 区域
    async def list_regions(self):
        cache_data = await self.cache.get_regions()
        if cache_data:
            return cache_data

        data = self.client.list_regions()
        await self.cache.set_regions(data)
        return data

    # 可用区
    async def list_zones(self, region_id):
        cache_data = await self.cache.get_zones(region_id)
        if cache_data:
            return cache_data

        data = self.client.list_zones(region_id)
        await self.cache.set_zones(region_id, data)
        return data

    # 镜像
    async def list_images(
        self,
        region_id: str,
        instance_type_id: str,
        architecture: str = None,
    ):
        cache_data = await self.cache.get_images(region_id)
        if cache_data:
            return cache_data

        data = self.client.list_images(region_id, instance_type_id, architecture)
        await self.cache.set_images(region_id, data)
        return data

    # 全量规格
    async def list_instance_types(self, region_id):
        # await self.cache.del_instance_types(region_id)
        cache_data = await self.cache.get_instance_types(region_id)
        if cache_data:
            return cache_data

        data = self.client.list_instance_types()
        await self.cache.set_instance_types(region_id, data)
        return data


    # 可用区规格
    async def list_available_instance_types(
        self,
        region_id,
        zone_id,
        instance_charge_type,
        disk_category
    ):
        # await self.cache.del_available_types(region_id)
        cache_data = await self.cache.get_available_types(region_id)
        if cache_data:
            return cache_data

        data = self.client.list_available_instance_types(region_id, zone_id, instance_charge_type.value, disk_category)
        await self.cache.set_available_types(region_id, data)
        return data

    # 系统盘种类
    async def list_system_disk_categories(self, region_id, zone_id, instance_type_id, instance_charge_type):
        cache_data = await self.cache.get_system_disks(region_id)
        if cache_data:
            return cache_data

        data = self.client.list_system_disk_categories(region_id, zone_id, instance_type_id, instance_charge_type.value)
        await self.cache.set_system_disks(region_id, data)
        return data


    # 服务器价格
    async def cloud_price(
        self,
        region_id,
        instance_type_id,
        disk_category,
        system_disk_size,
        instance_charge_type,
        period):
        cache_data = await self.cache.get_cloud_prices(region_id)
        if cache_data:
            return cache_data

        data = self.client.cloud_price(
            region_id, instance_type_id,disk_category,
            system_disk_size, instance_charge_type, period
        )
        await self.cache.set_cloud_prices(region_id, data)
        return data

    # 实例规格价格
    def instance_price(
        self,
        region_id,
        instance_type,
        instance_charge_type,
        system_disk_category,
        period: int = 1):
        return self.client.instance_price(
            region_id,
            instance_type,
            instance_charge_type,
            system_disk_category,
            period
        )

    # 公网eip价格
    def eip_price(self, region_id: str, bandwidth: int, internet_charge_type: str):
        price = self.client.client_eip_price(
            region_id,
            bandwidth,
            internet_charge_type
        )
        # logger.info(f'来获取价格吧 --------------》〉》〉》〉》〉{price}')
        return price
