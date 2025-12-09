import json
import math
import logging
import time
from typing import List
from services.redis_client import get_redis_client

logger = logging.getLogger(__name__)


def check_prime(number: int, previous_primes: List[int]) -> bool:
    is_prime = True
    limit = int(math.sqrt(number)) + 1
    for prime in previous_primes:
        if prime <= limit and number % prime == 0:
            is_prime = False
            break
    return is_prime


def load_cached_primes(redis_client):
    data = redis_client.get("primes:current")
    if not data:
        return []
    try:
        return json.loads(data)
    except Exception:
        return []


def save_cached_primes(redis_client, primes: List[int]):
    redis_client.set("primes:current", json.dumps(primes))


def compute_first_n_primes(n: int, request_id: str = ""):
    """Compute first n primes using cached primes in Redis for reuse.

    Returns the list of first n primes.
    Includes a 10-second sleep to emulate a longer-running background job.
    """
    redis_client = get_redis_client()

    # Use a lock to avoid concurrent writes to the cached primes
    lock = redis_client.lock("primes:lock", blocking_timeout=30)
    with lock:
        primes = load_cached_primes(redis_client)

        if len(primes) >= n:
            logger.info(f"[{request_id}] Using cached primes (have {len(primes)} >= need {n})")
            return primes[:n]

        # Start from last prime + 1
        if not primes:
            primes = [2]
        number = primes[-1] + 1
        count = len(primes)

        logger.info(f"[{request_id}] Starting computation from {number}, have {count} primes")
        
        # Sleep 10 seconds to emulate a longer-running background job
        logger.info(f"[{request_id}] Sleeping 10 seconds to emulate background processing...")
        time.sleep(10)
        logger.info(f"[{request_id}] Resuming computation after sleep")

        while count < n:
            if check_prime(number, primes):
                primes.append(number)
                count += 1
                if count % 100 == 0:
                    # Periodically persist progress
                    save_cached_primes(redis_client, primes)
                    logger.info(f"[{request_id}] Persisted progress: {count} primes")
            number += 1

        # Save final list
        save_cached_primes(redis_client, primes)
        logger.info(f"[{request_id}] Computation finished: {len(primes)} primes saved")
        return primes[:n]
