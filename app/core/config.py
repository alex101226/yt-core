# app/core/config.py
import os

from pathlib import Path as FilePath

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

BASE_DIR = FilePath(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    ENV: str = "development"
    HOST: str
    PORT: int
    DEBUG: bool

    API_PREFIX: str = "/api"
    LOG_LEVEL: str = "info"

    # 多数据库配置
    DB_SSO_AUTH: str
    DB_CMP: str
    DB_HUB: str

    SSO_TABLE_PREFIX: str = 'ss_'
    CMP_TABLE_PREFIX: str = 'cm_'
    HUB_TABLE_PREFIX: str = 'hub_'

    # jwt配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # radis配置
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = None
    REDIS_EXPIRE: int = 2592000  # 30天

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / f".env.{os.getenv('ENV', 'development')}",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
