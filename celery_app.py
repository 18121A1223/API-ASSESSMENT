import os
import logging
import json
from celery import Celery
from services.redis_client import get_redis_client
from services.prime_service import compute_first_n_primes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# TTL for request state in Redis (10 minutes)
REQUEST_TTL_SECONDS = 600

celery = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Windows compatibility: use 'solo' pool (single-threaded) to avoid prefork multiprocessing issues
# On Linux/WSL, you can change worker_pool to 'prefork' or 'threads' for true concurrency
celery.conf.update(
    worker_pool="solo",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery.task(bind=True)
def compute_primes_task(self, request_id: str, n: int):
    redis_client = get_redis_client()
    key = f"request:{request_id}"
    try:
        # mark processing and refresh TTL
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "processing", "result": None}))

        primes = compute_first_n_primes(n, request_id=request_id)

        # Save result and mark done, refresh TTL
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "done", "result": primes}))
        logger.info(f"[{request_id}] Task done, computed {len(primes)} primes")
        return primes
    except Exception as exc:
        logger.exception(f"[{request_id}] Task failed: {exc}")
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "failed", "result": None, "error": str(exc)}))
        raise
