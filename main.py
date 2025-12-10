import logging
import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, REGISTRY
from api import health_router
from api import tasks_router
from api.metrics_api import metrics_router
from observability import setup_opentelemetry, instrument_fastapi, instrument_redis, instrument_celery, PROMETHEUS_PORT

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry and instrumentation
logger.info("Initializing OpenTelemetry...")
setup_opentelemetry()
instrument_redis()
instrument_celery()

# Initialize FastAPI app
app = FastAPI(
    title="Prime Numbers API",
    description="FastAPI application to calculate N prime numbers with background task processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Instrument FastAPI
instrument_fastapi(app)

# Register routers
app.include_router(health_router)
app.include_router(tasks_router)
app.include_router(metrics_router)


# Prometheus metrics endpoint
@app.get("/metrics", tags=["monitoring"])
def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(REGISTRY), media_type="text/plain")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
