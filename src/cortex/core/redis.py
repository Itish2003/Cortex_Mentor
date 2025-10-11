import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings
from arq import ArqRedis

redis_pool: ArqRedis | None = None

async def create_redis_pool():
    global redis_pool
    redis_pool = await create_pool(RedisSettings())

async def close_redis_pool():
    if redis_pool:
        await redis_pool.close()

def get_redis():
    assert redis_pool is not None, "Redis pool is not initialized. Call create_redis_pool() first."
    return redis_pool
    