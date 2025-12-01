import json
from app.core.cache import get_redis
from app.core.config import settings

async def cache_set(key: str, value, expire=None):
    if expire is None:
        expire = settings.REDIS_EXPIRE

    redis = get_redis()
    await redis.set(key, json.dumps(value), ex=expire)


async def cache_get(key: str):
    redis = get_redis()
    raw = await redis.get(key)
    return json.loads(raw) if raw else None


async def cache_delete(key: str):
    redis = get_redis()  # 懒初始化获取 Redis
    return await redis.delete(key)
