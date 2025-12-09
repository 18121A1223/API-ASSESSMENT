import os
import redis

# Redis configuration for the application. Keep this at project root to
# make it the single source of truth for Redis connection settings.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_redis_client():
    """Return a redis.Redis client configured from `REDIS_URL`.

    Use `decode_responses=True` so values are returned as strings.
    """
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)
