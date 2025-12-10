import os
import logging
import json
from celery import Celery
from services.redis_client import get_redis_client
from services.prime_service import compute_first_n_primes
from metrics import task_submissions_total

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

# Configuration for Celery
# Using threads pool for cross-platform compatibility (Windows, Linux, macOS)
# Docker containers will use threads pool with 4 concurrent workers per container
celery.conf.update(
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
        task_submissions_total.labels(status="started").inc()
        
        # mark processing and refresh TTL
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "processing", "result": None}))

        primes = compute_first_n_primes(n, request_id=request_id)

        # Save result and mark done, refresh TTL
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "done", "result": primes}))
        logger.info(f"[{request_id}] Task done, computed {len(primes)} primes")
        
        task_submissions_total.labels(status="completed").inc()
        return primes
    except Exception as exc:
        logger.exception(f"[{request_id}] Task failed: {exc}")
        redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": n, "status": "failed", "result": None, "error": str(exc)}))
        
        task_submissions_total.labels(status="failed").inc()
        raise
