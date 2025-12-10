"""
Custom application metrics using Prometheus client library.

Tracks prime computation metrics, request counts, and task execution times.
"""

import os
import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

OTEL_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() == "true"

if OTEL_ENABLED:
    # Task submission metrics
    task_submissions_total = Counter(
        "prime_task_submissions_total",
        "Total number of prime computation tasks submitted",
        ["status"]
    )
    
    task_duration_seconds = Histogram(
        "prime_task_duration_seconds",
        "Time spent computing primes (seconds)",
        ["n_primes"],
        buckets=(1, 5, 10, 30, 60, 120, 300, 600)
    )
    
    primes_computed_total = Counter(
        "prime_numbers_computed_total",
        "Total number of prime numbers computed",
        ["computation_type"]  # cached, computed
    )
    
    cache_hits_total = Counter(
        "prime_cache_hits_total",
        "Number of cache hits for prime computation",
    )
    
    cache_misses_total = Counter(
        "prime_cache_misses_total",
        "Number of cache misses for prime computation",
    )
    
    active_computations = Gauge(
        "prime_active_computations",
        "Number of currently active prime computation tasks"
    )
    
    redis_operations_total = Counter(
        "redis_operations_total",
        "Total Redis operations",
        ["operation", "status"]  # operation: set, get, delete; status: success, failure
    )
    
    request_ttl_seconds = Gauge(
        "request_ttl_seconds",
        "TTL in seconds for request state in Redis",
    )
    
    # API endpoint metrics (custom, since FastAPI instrumentation may not capture all details)
    api_requests_total = Counter(
        "api_requests_total",
        "Total API requests",
        ["method", "endpoint", "status"]
    )
    
    api_request_duration_seconds = Histogram(
        "api_request_duration_seconds",
        "API request duration in seconds",
        ["method", "endpoint"],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
    )
    
    logger.info("Prometheus metrics initialized")
else:
    logger.info("Metrics disabled (OTEL_ENABLED=false)")
    
    # Dummy metrics that do nothing when disabled
    class DummyCounter:
        def labels(self, **kwargs):
            return self
        def inc(self, amount=1):
            pass
    
    class DummyHistogram:
        def labels(self, **kwargs):
            return self
        def observe(self, value):
            pass
    
    class DummyGauge:
        def labels(self, **kwargs):
            return self
        def set(self, value):
            pass
        def inc(self, amount=1):
            pass
        def dec(self, amount=1):
            pass
    
    task_submissions_total = DummyCounter()
    task_duration_seconds = DummyHistogram()
    primes_computed_total = DummyCounter()
    cache_hits_total = DummyCounter()
    cache_misses_total = DummyCounter()
    active_computations = DummyGauge()
    redis_operations_total = DummyCounter()
    request_ttl_seconds = DummyGauge()
    api_requests_total = DummyCounter()
    api_request_duration_seconds = DummyHistogram()
