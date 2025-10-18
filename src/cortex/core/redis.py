import redis.asyncio as redis
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis

async def create_redis_pool() -> ArqRedis:
    """Creates and returns a new ARQ Redis pool."""
    return await create_pool(RedisSettings())

async def close_redis_pool(pool: ArqRedis | None):
    """Closes the given Redis pool if it exists."""
    if pool:
        await pool.close()
    