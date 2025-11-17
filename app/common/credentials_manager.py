# app/common/credentials_manager.py
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredConfig
from alibabacloud_tea_openapi import models as open_api_models

class CredentialsManager:
    """
    云厂商通用凭证管理工具类：
    - 动态创建阿里云/腾讯云等认证客户端
    """

    @staticmethod
    def build_aliyun_client(access_key_id: str, access_key_secret: str) -> CredentialClient:
        """创建阿里云 CredentialClient"""
        return CredentialClient(
            CredConfig(
                type='access_key',
                access_key_id=access_key_id,
                access_key_secret=access_key_secret
            )
        )

    @staticmethod
    def build_aliyun_product_config(cred_client: CredentialClient, endpoint: str) -> open_api_models.Config:
        """构建阿里云产品配置对象"""
        return open_api_models.Config(credential=cred_client, endpoint=endpoint)
