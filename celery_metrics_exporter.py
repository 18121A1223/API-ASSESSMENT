"""
Celery Metrics Exporter
Runs a Celery worker alongside a Prometheus metrics HTTP server.
Metrics recorded by the Celery worker are exposed on port 8001 via the shared REGISTRY.
"""

import os
import sys
import logging
import threading
import time
from prometheus_client import start_http_server

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_metrics_server():
    """Start Prometheus metrics HTTP server on port 8001."""
    logger.info("Starting Prometheus metrics HTTP server on port 8001...")
    try:
        start_http_server(8001)
        logger.info("Metrics server started successfully")
    except Exception as e:
        logger.exception(f"Failed to start metrics server: {e}")
        sys.exit(1)

def start_celery_worker():
    """Start Celery worker process."""
    logger.info("Starting Celery worker...")
    
    # Import Celery app to ensure metrics are registered in REGISTRY
    from celery_app import celery
    from celery import signals
    
    @signals.worker_ready.connect
    def worker_ready(**kwargs):
        logger.info("Celery worker is ready to accept tasks")
    
    # Start worker with configuration from celery_app
    celery.worker_main([
        "worker",
        "--loglevel=info",
        "--pool=threads",
        "--concurrency=2",
        "--hostname=worker1@%h"
    ])

if __name__ == "__main__":
    # Start metrics server in a background thread
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=False)
    metrics_thread.start()
    
    # Give the metrics server a moment to start
    time.sleep(1)
    
    # Start Celery worker in the main thread (blocking)
    logger.info("Celery metrics exporter started")
    start_celery_worker()
