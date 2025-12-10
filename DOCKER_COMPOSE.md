# Docker Compose - Complete Stack

## One Command to Start Everything

This Docker Compose setup runs:
- ✅ FastAPI application (port 8000)
- ✅ Celery worker with metrics exporter (port 8001 for metrics)
- ✅ Redis (message broker & cache, port 6379)
- ✅ Prometheus (metrics scraper, port 9090)
- ✅ VictoriaMetrics (time-series database, port 8428)
- ✅ Grafana (dashboards, port 3000)
- ✅ Redis Exporter (Redis metrics, port 9121)

## Start Everything

```powershell
docker-compose up -d
```

Wait 60-90 seconds for all services to be healthy.

## Check Status

```powershell
docker-compose ps
```

All services should show `healthy` or `Up`.

## Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Prometheus Targets** | http://localhost:9090/targets | - |
| **VictoriaMetrics** | http://localhost:8428 | - |
| **Celery Metrics** | http://localhost:8001/metrics | - |
| **Redis Exporter** | http://localhost:9121/metrics | - |

## Submit a Task (PowerShell)

```powershell
# Submit task (compute first N primes)
$response = Invoke-WebRequest -Uri "http://localhost:8000/tasks" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"n":100}'
$requestId = ($response.Content | ConvertFrom-Json).request_id
echo "Task ID: $requestId"

# Check status
Invoke-WebRequest -Uri "http://localhost:8000/tasks/$requestId"
```

## Monitor Metrics

```powershell
# Via JSON API (FastAPI)
Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/summary" | ConvertFrom-Json

# Via Prometheus Queries
# Open http://localhost:9090
# Example: query "prime_cache_hits_total"

# Via Grafana Dashboards
# Open http://localhost:3000
# Login: admin / admin
# Navigate to: Dashboards → Prime API Metrics
```

## Submit Multiple Tasks (Test Concurrency)

```powershell
# These will run in sequence (1 worker with 2 concurrent threads)
Invoke-WebRequest -Uri "http://localhost:8000/tasks" -Method POST -ContentType "application/json" -Body '{"n":100}'
Invoke-WebRequest -Uri "http://localhost:8000/tasks" -Method POST -ContentType "application/json" -Body '{"n":10000}'
Invoke-WebRequest -Uri "http://localhost:8000/tasks" -Method POST -ContentType "application/json" -Body '{"n":5000}'
Invoke-WebRequest -Uri "http://localhost:8000/tasks" -Method POST -ContentType "application/json" -Body '{"n":1000}'
```

## View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fastapi
docker-compose logs -f celery-worker-1
docker-compose logs -f prometheus
docker-compose logs -f grafana
docker-compose logs -f victoriametrics
```

## Stop Everything

```powershell
docker-compose down
```

## Stop and Remove All Data

```powershell
docker-compose down -v
```

---

## Architecture

```
User Request (http://localhost:8000/tasks)
    ↓
FastAPI Container (Port 8000)
    ↓
Redis Container (Port 6379)
    ↓
Celery Worker (Port 8001 metrics)
    ↓
Redis (result storage)
    ↓
Prometheus (Port 9090, scrapes metrics from :8000, :8001, :9121, :8428)
    ↓
VictoriaMetrics (Port 8428, stores time-series data)
    ↓
Grafana (Port 3000, visualizes dashboards)
```

## Celery Configuration

- **1 worker** (celery-worker-1)
- **Threads pool** (cross-platform compatible, works on Windows)
- **Concurrency: 2 threads** (optimized for local development, prevents laptop overload)
- **Metrics exposed on port 8001** (via celery_metrics_exporter.py)

## Scale Concurrency (Local Development)

Edit `celery_metrics_exporter.py` and modify the `--concurrency` parameter:

```python
celery.worker_main([
    "worker",
    "--loglevel=info",
    "--pool=threads",
    "--concurrency=4",  # Change this to 4, 8, etc.
    "--hostname=worker1@%h"
])
```

Then rebuild and restart:

```powershell
docker-compose down
docker-compose up -d
```

## Scale to Multiple Workers (Production)

Duplicate celery-worker-1 service in `docker-compose.yml`:

```yaml
celery-worker-2:
  build:
    context: .
    dockerfile: Dockerfile.celery
  container_name: celery-worker-2
  ports:
    - "8002:8001"  # Metrics on 8002
  environment:
    REDIS_URL: redis://redis:6379/0
    CELERY_BROKER_URL: redis://redis:6379/0
    CELERY_RESULT_BACKEND: redis://redis:6379/0
    OTEL_ENABLED: "true"
  volumes:
    - .:/app
  networks:
    - app
  depends_on:
    redis:
      condition: service_healthy
  command: python celery_metrics_exporter.py
```

Then update `monitoring/prometheus.yml` to scrape the new worker on port 8002.

## Metrics Available

Prometheus scrapes these targets automatically:
- **fastapi:8000/metrics** - FastAPI + Python runtime metrics
- **celery-worker-1:8001/metrics** - Celery task metrics + Python runtime
- **redis-exporter:9121/metrics** - Redis instance metrics
- **victoriametrics:8428/metrics** - VictoriaMetrics internal metrics

## Custom Metrics (Prime API)

Available custom metrics in Prometheus:
- `prime_task_submissions_total{status}` - Tasks started/completed/failed (counter)
- `prime_cache_hits_total` - Cache hits for prime calculations (counter)
- `prime_cache_misses_total` - Cache misses (counter)
- `prime_active_computations` - Currently running tasks (gauge)
- `prime_numbers_computed_total{computation_type}` - Total primes computed (cached/computed) (counter)
- `prime_task_duration_seconds` - Task execution time histogram
- `api_requests_total{method,endpoint,status}` - API request counts (counter)
- `api_request_duration_seconds{method,endpoint}` - API request latency (histogram)

## Example Prometheus Queries

```promql
# Task submission rate per minute
rate(prime_task_submissions_total[1m])

# Failed task rate
rate(prime_task_submissions_total{status="failed"}[5m])

# Cache hit ratio
prime_cache_hits_total / (prime_cache_hits_total + prime_cache_misses_total)

# Current active tasks
prime_active_computations

# Task completion rate
rate(prime_task_submissions_total{status="completed"}[5m])
```

## Troubleshooting

**Services not starting?**
```powershell
docker-compose logs
```

**Prometheus not scraping metrics?**
- Check http://localhost:9090/targets
- All targets should show "UP"

**Grafana dashboards empty?**
- Verify Prometheus datasource in Grafana (http://localhost:3000/admin/datasources)
- Confirm metrics exist: `http://localhost:9090/targets`

**Celery metrics not showing?**
- Check `http://localhost:8001/metrics` directly
- Verify Celery target is UP in Prometheus
- Restart Celery worker: `docker-compose restart celery-worker-1`

## Notes

- All containers are on `app` network (communicate by service name)
- Volumes persist data between restarts
- Health checks ensure services are stable
- Metrics are auto-collected by Prometheus every 10-15 seconds
- No local Python installation needed when using Docker Compose
- Optimized for local development (low resource usage)
