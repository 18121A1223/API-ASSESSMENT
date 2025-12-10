import json
import math
import logging
import time
from typing import List
from services.redis_client import get_redis_client
from metrics import (
    cache_hits_total, cache_misses_total, task_duration_seconds,
    primes_computed_total, active_computations
)

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


def get_largest_n_computed(redis_client) -> int:
    """Get the largest N for which primes have been fully computed."""
    data = redis_client.get("primes:largest_n")
    return int(data) if data else 0


def update_largest_n_computed(redis_client, n: int):
    """Update the largest N for which primes have been fully computed."""
    current_largest = get_largest_n_computed(redis_client)
    if n > current_largest:
        redis_client.set("primes:largest_n", str(n))


def compute_first_n_primes(n: int, request_id: str = ""):
    """Compute first n primes using cached primes in Redis for reuse.

    Returns the list of first n primes.
    Includes a 10-second sleep to emulate a longer-running background job.
    Records metrics for cache hits/misses and computation time.
    
    Strategy:
    - Tracks the largest N for which all primes have been fully computed (primes:largest_n)
    - If requested N is <= largest_n, immediately return cached primes (cache hit)
    - If requested N > largest_n, compute all primes up to N and update largest_n
    - Multiple concurrent tasks with different N values all work toward the global maximum
    """
    start_time = time.time()
    redis_client = get_redis_client()
    active_computations.inc()

    try:
        # Check if we already have all primes for this N
        largest_n_computed = get_largest_n_computed(redis_client)
        
        if largest_n_computed >= n:
            # We have computed all primes up to this N or beyond
            primes = load_cached_primes(redis_client)
            logger.info(f"[{request_id}] Cache hit: largest_n={largest_n_computed} >= requested={n}, returning {len(primes)} cached primes")
            cache_hits_total.inc()
            primes_computed_total.labels(computation_type="cached").inc(n)
            return primes[:n]

        # Cache miss - need to compute more primes
        cache_misses_total.inc()
        primes = load_cached_primes(redis_client)
        
        if not primes:
            primes = [2]
        
        count = len(primes)
        number = primes[-1] + 1

        logger.info(f"[{request_id}] Computing primes: largest_n={largest_n_computed}, requested={n}, have {count} primes, starting from {number}")
        
        # Sleep 10 seconds to emulate a longer-running background job
        logger.info(f"[{request_id}] Sleeping 10 seconds to emulate background processing...")
        time.sleep(10)
        logger.info(f"[{request_id}] Resuming computation after sleep")

        # Compute until we have at least N primes (or more if another task asks for more)
        while count < n:
            if check_prime(number, primes):
                primes.append(number)
                count += 1
                if count % 100 == 0:
                    # Periodically persist progress (non-blocking)
                    save_cached_primes(redis_client, primes)
                    logger.info(f"[{request_id}] Persisted progress: {count} primes")
            number += 1

        # Save final list and update largest_n marker
        save_cached_primes(redis_client, primes)
        update_largest_n_computed(redis_client, n)
        logger.info(f"[{request_id}] Computation finished: {n} primes computed and saved, largest_n updated")
        
        # Record metrics
        computed_count = n - largest_n_computed
        primes_computed_total.labels(computation_type="computed").inc(computed_count)
        duration = time.time() - start_time
        task_duration_seconds.labels(n_primes=str(n)).observe(duration)
        
        return primes[:n]
    finally:
        active_computations.dec()
