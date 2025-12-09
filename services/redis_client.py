"""Compatibility wrapper that re-exports `get_redis_client` from the
project-level `redis_config` module.

This avoids changing all callers that import from `services.redis_client`.
"""

try:
    from redis_config import get_redis_client  # project-level config (preferred)
except Exception:
    # Fallback: if redis_config isn't available on PYTHONPATH, provide a
    # minimal implementation so imports don't break during isolated tests.
    import os
    import redis

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    def get_redis_client():
        return redis.Redis.from_url(REDIS_URL, decode_responses=True)
