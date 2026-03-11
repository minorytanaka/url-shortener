from redis.asyncio import ConnectionPool, Redis

from app.config import settings

pool: ConnectionPool | None = None


def init_pool() -> None:
    global pool
    pool = ConnectionPool.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=settings.redis_max_connections,
    )


async def close_pool() -> None:
    if pool:
        await pool.aclose()


def get_redis() -> Redis:
    return Redis(connection_pool=pool)


async def cache_link(redis: Redis, short_id: str, original_url: str) -> None:
    """
    Сохранить маппинг short_id:url в Redis.
    """

    await redis.set(f"url:{short_id}", original_url, ex=settings.cache_ttl)


async def get_cached_url(redis: Redis, short_id: str) -> str | None:
    """
    Получить оригинальный URL из кэша.
    """

    return await redis.get(f"url:{short_id}")


async def increment_clicks(redis: Redis, short_id: str) -> None:
    """
    Инкрементировать счётчик кликов в Redis.
    """

    await redis.incr(f"clicks:{short_id}")


async def get_and_reset_clicks(redis: Redis, short_id: str) -> int:
    """
    Забрать счётчик кликов и сбросить в 0.
    """

    pipe = redis.pipeline()
    pipe.get(f"clicks:{short_id}")
    pipe.delete(f"clicks:{short_id}")
    results = await pipe.execute()
    return int(results[0] or 0)
