from redis.asyncio import Redis

redis: Redis | None = None


def get_redis() -> Redis:
    if redis is None:
        raise RuntimeError("Redis not initialized")

    return redis
