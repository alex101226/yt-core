# app/clients/cloud_client_factory.py
from app.clients.aliyun_client import AliyunClientFactory
# from app.clients.tencent_client import TencentClientFactory

class CloudClientFactory:
    """多云客户端工厂"""

    @staticmethod
    def create_client(provider_code: str, access_key_id: str, access_key_secret: str, endpoint: str):
        if provider_code == "aliyun":
            return AliyunClientFactory.create_client(access_key_id, access_key_secret, endpoint)
        # elif provider_code == "tencentcloud":
        #     return TencentClientFactory(access_key_id, access_key_secret, endpoint)
        else:
            raise ValueError(f"Unsupported cloud provider: {provider_code}")
