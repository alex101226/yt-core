# app/clients/cloud_client_factory.py
from app.clients.aliyun_client import AliyunClientFactory, AliyunClient

# from app.clients.tencent_client import TencentClientFactory

"""多云客户端工厂"""
class CloudClientFactory:
    _cache = {}

    @staticmethod
    def create_client(provider_code: str, access_key_id: str, access_key_secret: str, endpoint: str):
        cache_key = f"{provider_code}:{access_key_id}"
        if cache_key in CloudClientFactory._cache:
            return CloudClientFactory._cache[cache_key]

        if provider_code == "aliyun":
            client = AliyunClientFactory.create_client(access_key_id, access_key_secret, endpoint)
        # elif provider_code == "tencentcloud":
        #     client = TencentClientFactory.create_client(access_key_id, access_key_secret, endpoint)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider_code}")

        CloudClientFactory._cache[cache_key] = client
        return client