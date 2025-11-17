# app/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    ENV: str = "development"
    API_PREFIX: str = "/api"
    LOG_LEVEL: str = "info"

    # 多数据库配置
    DB_SSO_AUTH: str
    DB_PUBLIC: str
    DB_AUDIT_CENTER: str
    DB_CMP: str

    PUBLIC_TABLE_PREFIX: str = 'pu_'
    SSO_TABLE_PREFIX: str = 'ss_'
    AUDIT_TABLE_PREFIX: str = 'au_'
    CMP_TABLE_PREFIX: str = 'cm_'

    class Config:
        env_file = f".env.{os.getenv('ENV', 'development')}"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
