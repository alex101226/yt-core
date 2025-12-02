import json
from app.core.cache import get_redis
from app.core.config import settings
# 开机，关机，重启，创建镜像，开启ssh代理，克隆，更换镜像，修改管理密码，改包年包月，开启释放保护，释放
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
