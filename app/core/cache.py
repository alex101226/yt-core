import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings
from app.core.logger import logger

redis_client: Optional[aioredis.Redis] = None

# 云厂商，区域，可用区，云凭证，计费方式，带宽上限（这里还有个具体的宽带数值吧），名称，资源组，用户id，价格
# 在 FastAPI lifespan 中调用，用于初始化 Redis 连接池
def get_redis() -> aioredis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            max_connections=50,
        )
        logger.info(f"Redis connection: {redis_client}")
    return redis_client
