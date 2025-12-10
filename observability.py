"""
OpenTelemetry configuration and instrumentation setup.

This module initializes OpenTelemetry with Prometheus exporter for metrics collection
from FastAPI, Celery, Redis, and the application.
"""

import os
import logging
from typing import Optional

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

logger = logging.getLogger(__name__)

# Configuration from env vars
OTEL_ENABLED = os.getenv("OTEL_ENABLED", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8001"))
SERVICE_NAME = os.getenv("SERVICE_NAME", "prime-api")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


def setup_opentelemetry():
    """Initialize OpenTelemetry with Prometheus metrics exporter."""
    
    if not OTEL_ENABLED:
        logger.info("OpenTelemetry disabled via OTEL_ENABLED env var")
        return
    
    try:
        # Create resource
        resource = Resource.create({
            "service.name": SERVICE_NAME,
            "service.version": SERVICE_VERSION,
            "deployment.environment": ENVIRONMENT,
        })
        
        # Prometheus reader for metrics
        prometheus_reader = PrometheusMetricReader()
        
        # Create meter provider with Prometheus exporter
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[prometheus_reader],
        )
        
        logger.info(f"OpenTelemetry initialized with Prometheus exporter on port {PROMETHEUS_PORT}")
        
        return meter_provider, prometheus_reader
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}", exc_info=True)
        raise


def instrument_fastapi(app):
    """Instrument FastAPI application with OpenTelemetry."""
    
    if not OTEL_ENABLED:
        logger.info("FastAPI instrumentation disabled")
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument FastAPI: {e}", exc_info=True)


def instrument_celery():
    """Instrument Celery with OpenTelemetry."""
    
    if not OTEL_ENABLED:
        logger.info("Celery instrumentation disabled")
        return
    
    try:
        CeleryInstrumentor().instrument()
        logger.info("Celery instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument Celery: {e}", exc_info=True)


def instrument_redis():
    """Instrument Redis with OpenTelemetry."""
    
    if not OTEL_ENABLED:
        logger.info("Redis instrumentation disabled")
        return
    
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument Redis: {e}", exc_info=True)


def instrument_requests():
    """Instrument HTTP requests with OpenTelemetry."""
    
    if not OTEL_ENABLED:
        logger.info("Requests instrumentation disabled")
        return
    
    try:
        RequestsInstrumentor().instrument()
        logger.info("HTTP requests instrumented with OpenTelemetry")
    except Exception as e:
        logger.error(f"Failed to instrument requests: {e}", exc_info=True)
