"""
Metrics API endpoints for detailed monitoring and observability.

Exposes custom JSON endpoints for metrics visualization and analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from prometheus_client import REGISTRY, CollectorRegistry
import json
from services.redis_client import get_redis_client
from metrics import (
    cache_hits_total, cache_misses_total, task_duration_seconds,
    primes_computed_total, active_computations, task_submissions_total
)

metrics_router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@metrics_router.get("/health")
def metrics_health() -> Dict[str, Any]:
    """Check metrics collection health and Redis connectivity."""
    try:
        redis_client = get_redis_client()
        redis_info = redis_client.info()
        
        return {
            "status": "healthy",
            "redis": {
                "connected": True,
                "used_memory_mb": redis_info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_commands_processed": redis_info.get("total_commands_processed", 0)
            },
            "metrics": {
                "otel_enabled": True,
                "prometheus_registry_initialized": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics health check failed: {str(e)}")


@metrics_router.get("/summary")
def metrics_summary() -> Dict[str, Any]:
    """Get a summary of key application metrics."""
    try:
        redis_client = get_redis_client()
        
        # Get redis cached data
        largest_n = redis_client.get("primes:largest_n")
        largest_n_int = int(largest_n) if largest_n else 0
        
        primes_data = redis_client.get("primes:current")
        primes_count = 0
        if primes_data:
            try:
                primes = json.loads(primes_data)
                primes_count = len(primes)
            except:
                pass
        
        # Count pending tasks (approximate via Redis keys)
        task_keys = redis_client.keys("request:*")
        task_count = len(task_keys) if task_keys else 0
        
        return {
            "primes_computation": {
                "largest_n_computed": largest_n_int,
                "total_primes_cached": primes_count,
                "active_computations": int(active_computations._value.get() if hasattr(active_computations, '_value') else 0)
            },
            "pending_tasks": task_count,
            "redis_memory": {
                "used_mb": redis_client.info().get("used_memory", 0) / (1024 * 1024),
                "peak_mb": redis_client.info().get("used_memory_peak", 0) / (1024 * 1024)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")


@metrics_router.get("/performance")
def metrics_performance() -> Dict[str, Any]:
    """Get performance metrics for prime computation tasks."""
    try:
        metrics_data = {}
        
        # Collect metrics from Prometheus registry
        for collector in REGISTRY._collector_to_names:
            for metric in collector.collect():
                if metric.name.startswith("prime_"):
                    for sample in metric.samples:
                        if sample.name not in metrics_data:
                            metrics_data[sample.name] = {
                                "type": metric.type,
                                "help": metric.documentation,
                                "value": sample.value,
                                "labels": sample.labels
                            }
                        else:
                            # For metrics with multiple samples, store as list
                            if not isinstance(metrics_data[sample.name], list):
                                metrics_data[sample.name] = [metrics_data[sample.name]]
                            metrics_data[sample.name].append({
                                "type": metric.type,
                                "help": metric.documentation,
                                "value": sample.value,
                                "labels": sample.labels
                            })
        
        return metrics_data if metrics_data else {"message": "No metrics collected yet"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@metrics_router.get("/cache-stats")
def cache_statistics() -> Dict[str, Any]:
    """Get detailed cache hit/miss statistics."""
    try:
        redis_client = get_redis_client()
        
        # Get cache counters (if available from metrics)
        cache_hits = 0
        cache_misses = 0
        
        for collector in REGISTRY._collector_to_names:
            for metric in collector.collect():
                if metric.name == "prime_cache_hits_total":
                    for sample in metric.samples:
                        cache_hits += int(sample.value)
                elif metric.name == "prime_cache_misses_total":
                    for sample in metric.samples:
                        cache_misses += int(sample.value)
        
        total = cache_hits + cache_misses
        hit_rate = (cache_hits / total * 100) if total > 0 else 0
        
        return {
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "total_operations": total,
            "hit_rate_percent": round(hit_rate, 2),
            "miss_rate_percent": round(100 - hit_rate, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")


@metrics_router.get("/task-stats")
def task_statistics() -> Dict[str, Any]:
    """Get detailed task execution statistics."""
    try:
        redis_client = get_redis_client()
        task_keys = redis_client.keys("request:*")
        
        statuses = {
            "pending": 0,
            "processing": 0,
            "done": 0,
            "failed": 0
        }
        
        for key in task_keys or []:
            try:
                data = redis_client.get(key)
                if data:
                    task_data = json.loads(data)
                    status = task_data.get("status", "unknown")
                    if status in statuses:
                        statuses[status] += 1
            except:
                pass
        
        total = sum(statuses.values())
        
        return {
            "task_counts": statuses,
            "total_tasks": total,
            "completion_rate_percent": round((statuses["done"] / total * 100) if total > 0 else 0, 2),
            "failure_rate_percent": round((statuses["failed"] / total * 100) if total > 0 else 0, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task statistics: {str(e)}")


@metrics_router.get("/redis-stats")
def redis_statistics() -> Dict[str, Any]:
    """Get Redis server statistics."""
    try:
        redis_client = get_redis_client()
        info = redis_client.info()
        
        return {
            "server": {
                "redis_version": info.get("redis_version", "unknown"),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0)
            },
            "memory": {
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                "used_memory_peak_mb": info.get("used_memory_peak", 0) / (1024 * 1024),
                "memory_fragmentation_ratio": info.get("mem_fragmentation_ratio", 0)
            },
            "stats": {
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
                "rejected_connections": info.get("rejected_connections", 0)
            },
            "replication": {
                "role": info.get("role", "unknown"),
                "connected_slaves": info.get("connected_slaves", 0)
            },
            "keys": {
                "database_0_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                "total_keys_estimate": sum(
                    info.get(f"db{i}", {}).get("keys", 0) 
                    for i in range(16) 
                    if f"db{i}" in info
                )
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Redis statistics: {str(e)}")


@metrics_router.get("/all")
def all_metrics() -> Dict[str, Any]:
    """Get all collected metrics in a single response."""
    try:
        return {
            "summary": metrics_summary(),
            "cache_stats": cache_statistics(),
            "task_stats": task_statistics(),
            "redis_stats": redis_statistics(),
            "performance": metrics_performance()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to collect all metrics: {str(e)}")
