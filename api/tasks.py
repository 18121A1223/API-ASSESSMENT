from fastapi import APIRouter, HTTPException
import uuid
import json
import logging
from typing import Optional
from services.redis_client import get_redis_client
from celery_app import compute_primes_task
from models.task import CreateTaskRequest, TaskStatusResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

# TTL for request state in Redis (10 minutes)
REQUEST_TTL_SECONDS = 600


@router.post("", status_code=202)
def create_task(payload: CreateTaskRequest):
    request_id = uuid.uuid4().hex
    redis_client = get_redis_client()

    # store initial request state with 10-minute TTL
    key = f"request:{request_id}"
    redis_client.setex(key, REQUEST_TTL_SECONDS, json.dumps({"n": payload.n, "status": "pending", "result": None}))

    # enqueue celery task
    compute_primes_task.delay(request_id, payload.n)
    logger.info(f"[{request_id}] Enqueued task for n={payload.n}, TTL={REQUEST_TTL_SECONDS}s")
    return {"request_id": request_id}


@router.get("/{request_id}")
def get_task_status(request_id: str):
    redis_client = get_redis_client()
    key = f"request:{request_id}"
    data = redis_client.get(key)
    if not data:
        raise HTTPException(status_code=404, detail="Request ID not found")
    try:
        payload = json.loads(data)
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupt data")

    return payload
