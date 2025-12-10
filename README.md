# API-ASSESSMENT: FastAPI + Celery Prime Numbers Service

A FastAPI application that computes the first N prime numbers using Celery background tasks and Redis for caching and state management, with comprehensive observability via OpenTelemetry, Prometheus, VictoriaMetrics, and Grafana.

## Overview

This project demonstrates:
- **FastAPI** for HTTP API endpoints
- **Celery** for asynchronous background task processing
- **Redis** for task queue, result storage, and prime number caching
- **Optimized prime computation** with smart caching (reuses previously computed primes)
- **Request tracking** with unique IDs and comprehensive logging
- **OpenTelemetry instrumentation** for metrics, traces, and logs
- **Prometheus exporters** for metrics collection
- **VictoriaMetrics** for time-series data storage
- **Grafana dashboards** for visualization and monitoring

## Quick Start

### Manual Setup

```powershell
# 1. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Start Docker Compose stack
docker-compose -f docker-compose.monitoring.yml up -d

# 3. Start FastAPI (Terminal 1)
python -m uvicorn main:app --reload

# 4. Start Celery Worker (Terminal 2)
celery -A celery_app worker --loglevel=info

# 5. Access services
# Grafana:     http://localhost:3000 (admin/admin)
# API Docs:    http://localhost:8000/docs
# Prometheus:  http://localhost:9090
# VictoriaMetrics: http://localhost:8428
```

See `RUN.md` for detailed step-by-step instructions.

---
## 📡 Service URLs & Access

### Running Services with Docker Compose

Once `docker-compose up -d` is running, access these services:

| Service | URL | Purpose | Credentials |
|---------|-----|---------|-------------|
| **FastAPI App** | http://localhost:8000 | Main application - submit tasks | N/A |
| **FastAPI Docs** | http://localhost:8000/docs | Interactive API documentation (Swagger) | N/A |
| **FastAPI Health** | http://localhost:8000/health | Health check | N/A |
| **Grafana Dashboards** | http://localhost:3000 | Visualization & monitoring | admin / admin |
| **Prometheus** | http://localhost:9090 | Metrics query interface | N/A |
| **Prometheus Targets** | http://localhost:9090/targets | Scrape targets status | N/A |
| **VictoriaMetrics API** | http://localhost:8428 | Time-series database API | N/A |
| **Redis Metrics** | http://localhost:9121/metrics | Redis metrics (Prometheus format) | N/A |

### Common API Endpoints

**Submit a task to compute primes:**
```bash
POST http://localhost:8000/tasks
Content-Type: application/json

{"n": 100}
```

**Check task status:**
```bash
GET http://localhost:8000/tasks/{request_id}
```

**Get metrics summary:**
```bash
GET http://localhost:8000/api/metrics/summary
```

**View all metrics:**
```bash
GET http://localhost:8000/api/metrics/all
```

**Grafana Login:**
- Username: `admin`
- Password: `admin`
- Access dashboards: Prime API Metrics, Redis Metrics


## Observability & Monitoring Architecture

### Complete Observability Stack

#### **1. OpenTelemetry (OTEL) Instrumentation**

Automatic tracing and metrics collection for:
- **FastAPI**: Request path, method, status code, duration
- **Celery**: Task name, status, execution time, arguments
- **Redis**: Command type, latency, success/failure
- **HTTP Requests**: Outbound request tracking

Location: `observability.py`

#### **2. Custom Prometheus Metrics**

Application-specific metrics tracked:

| Metric | Type | Purpose |
|--------|------|---------|
| `prime_task_submissions_total` | Counter | Tasks submitted (by status: started, completed, failed) |
| `prime_task_duration_seconds` | Histogram | Task execution time (buckets: 1s, 5s, 10s, 30s, 60s, 120s, 300s, 600s) |
| `prime_numbers_computed_total` | Counter | Primes computed vs cached |
| `prime_cache_hits_total` | Counter | Successful cache retrievals |
| `prime_cache_misses_total` | Counter | Cache misses requiring computation |
| `prime_active_computations` | Gauge | Currently running tasks |
| `redis_operations_total` | Counter | Redis operations by type and status |
| `api_requests_total` | Counter | HTTP requests by method/endpoint/status |
| `api_request_duration_seconds` | Histogram | API latency (buckets: 0.01s to 5s) |

Location: `metrics.py`

#### **3. Prometheus**

**What it does:**
- Scrapes metrics from FastAPI (`/metrics` endpoint)
- Collects metrics from Celery, Redis Exporter, and VictoriaMetrics
- Stores time-series data (default: 15 days)
- Evaluates alert rules
- Provides query interface (PromQL)

**Access:** http://localhost:9090

**Key sections:**
- **Targets** (http://localhost:9090/targets) - Shows all scrape targets (FastAPI, Celery, Redis Exporter, VictoriaMetrics)
- **Graph** (http://localhost:9090/graph) - Query metrics with PromQL
- **Alerts** (http://localhost:9090/alerts) - View alert status
- **Status** (http://localhost:9090/status) - Configuration details

**Configured scrape targets:**
```
fastapi:8000/metrics       (15s interval)
celery:8001                (15s interval)
redis-exporter:9121        (15s interval)
victoriametrics:8428/metrics (15s interval)
```

---

## Load testing with Locust

This project includes a Locust test file at `monitoring/locust/locustfile.py` that:
- Submits compute tasks to `POST /tasks` and stores the returned `request_id`;
- Polls `GET /tasks/{request_id}` until completion;
- Occasionally polls `/metrics`.

Two ways to run Locust are supported:

1) Run Locust as a Docker service (recommended for consistency)

  - The `docker-compose.yml` includes a `locust` service that mounts `monitoring/locust` and exposes the Locust web UI on port `8089`.

  Start the full stack including Locust:
  ```powershell
  cd "c:\Users\Dharaneshwar\Desktop\Assessment\wealthy\API-ASSESSMENT"
  docker compose up -d
  ```

  Open the Locust web UI at: http://localhost:8089
  - Enter the number of users and spawn rate, then click **Start swarming**.

  To stop Locust only:
  ```powershell
  docker compose stop locust
  ```

2) Run Locust locally (web UI) — useful for interactive debugging

  - Install Locust locally (recommended inside a virtualenv):
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install locust
  ```

  - Run Locust pointing at the app running in Docker Compose:
  ```powershell
  locust -f monitoring/locust/locustfile.py --host http://localhost:8000
  ```

  - Open http://localhost:8089 and start the test.

Headless runs (CI / automation)
--------------------------------
If you want to execute Locust headless (no web UI) and save CSV results:

```powershell
locust -f monitoring/locust/locustfile.py --headless -u 50 -r 5 --run-time 5m --host http://localhost:8000 --csv=locust-output
```

Notes & tips
- If Locust runs inside Docker and needs to reach services in the Compose network, use `--host http://fastapi` (service name) instead of `localhost`.
- The included `locustfile.py` polls task status; avoid extremely aggressive polling per user if you want to simulate realistic client behavior.
- Monitor `fastapi` logs during load testing:

```powershell
docker logs -f fastapi
```

If you'd like, I can:
- Add environment variables to the `locust` service in `docker-compose.yml` to make `-u`, `-r`, and `--run-time` configurable without editing the compose file.
- Add a short `monitoring/locust/README.md` with these instructions.

**Alert rules configured:**
- HighTaskFailureRate (> 10% failures in 5m)
- SlowTaskExecution (p95 duration > 60s)
- LowCacheHitRate (< 50% in 10m)
- RedisHighErrorRate (> 1% errors in 5m)
- HighAPIErrorRate (> 5% 5xx in 5m)

#### **4. VictoriaMetrics**

**What it does:**
- Long-term metrics storage (30-day retention)
- Optimized time-series database
- Complements/replaces Prometheus storage
- High compression ratio (1GB+ data in minimal space)

**Access:** http://localhost:8428

**Key sections:**
- **vminsert** - Metrics ingestion
- **vmselect** - Metrics querying
- **vmstorage** - Data storage
- **Query** (http://localhost:8428/select/0/prometheus/graph) - Same PromQL as Prometheus

#### **5. Grafana**

**What it does:**
- Visualization platform
- Pre-built dashboards for monitoring
- Real-time data display
- Alert annotations
- User-friendly dashboard creation

**Access:** http://localhost:3000
**Login:** admin / admin

**Pre-configured datasources:**
- Prometheus (primary metrics source)
- VictoriaMetrics (secondary/long-term storage)

**Pre-built dashboards:**

1. **Prime API Metrics Dashboard** (6 panels)
   - Task Submission & Completion Rate (timeseries)
   - Cache Hit Rate % (gauge with thresholds)
   - Task Duration Percentiles (p50, p95, p99)
   - Active Computations (stat)
   - Task Status Distribution (stacked area)
   - Primes Computed vs Cached (stacked area)

2. **Prime API Overview** (alternative view)
   - Similar panels focused on API health metrics

3. **Redis Metrics Dashboard** (5 panels)
   - Connected Clients (gauge)
   - Used Memory (gauge)
   - Commands Per Second (rate)
   - Keys per Database (breakdown)
   - Command Latency (histogram)

**Where to find what:**
- Click "Dashboards" (left sidebar) → Select dashboard
- Use "Explore" for ad-hoc queries
- Check "Alerts" for active alerts
- View "Annotations" for events

#### **6. Redis Exporter**

**What it does:**
- Exports Redis server metrics to Prometheus format
- Monitors: memory, clients, commands, latency, replication

**Metrics exported:**
- `redis_connected_clients` - Active client connections
- `redis_used_memory` - Memory usage in bytes
- `redis_commands_processed_total` - Total commands executed
- `redis_db_keys` - Keys per database
- `redis_commands_duration_seconds` - Command latency

**Access:** http://localhost:9121 (Prometheus format)

---

## JSON Metrics API

Custom `/api/metrics/*` endpoints for JSON-based monitoring:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/metrics/health` | System health check (Redis, Prometheus) |
| `GET /api/metrics/summary` | High-level overview (largest_n, cached_primes, active tasks) |
| `GET /api/metrics/cache-stats` | Cache hit/miss rates with percentages |
| `GET /api/metrics/task-stats` | Task status breakdown (pending, done, failed) |
| `GET /api/metrics/redis-stats` | Redis server health & memory |
| `GET /api/metrics/performance` | Raw Prometheus metrics from registry |
| `GET /api/metrics/all` | All metrics combined |

**Example:**
```powershell
curl http://localhost:8000/api/metrics/summary
```

---

## API Endpoints

### Task Submission

**POST /tasks**

Submit a job to compute first N primes.

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"n": 100}'
```

**Response:**
```json
{
  "request_id": "a1b2c3d4e5f6"
}
```

### Task Status

**GET /tasks/{request_id}**

Check task status and result.

```bash
curl http://localhost:8000/tasks/a1b2c3d4e5f6
```

**Responses:**
- `pending` - Queued, waiting to process
- `processing` - Celery worker executing
- `done` - Completed, result available
- `failed` - Error occurred

### Health Check

**GET /health**

```bash
curl http://localhost:8000/health
```

### Prometheus Metrics

**GET /metrics**

Raw Prometheus format metrics.

```bash
curl http://localhost:8000/metrics
```

### API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Configuration


### Redis URL

Redis connection is configured in `redis_config.py`. Default: `redis://localhost:6379/0`

To use a different Redis instance, set the `REDIS_URL` environment variable:

```powershell
$env:REDIS_URL = 'redis://hostname:6379/1'
```

The project re-exports `get_redis_client()` from `redis_config.py` via `services/redis_client.py` so all imports remain compatible.

## API Endpoints

### Submit a Task

**POST /tasks**

Submit a job to compute the first `n` prime numbers.

```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{"n": 100}'
```

**Response (HTTP 202):**
```json
{
  "request_id": "a1b2c3d4e5f6"
}
```

### Check Task Status

**GET /tasks/{request_id}**

Check the status and result of a submitted task.

```bash
curl "http://localhost:8000/tasks/a1b2c3d4e5f6"
```

**Response (pending):**
```json
{
  "n": 100,
  "status": "pending",
  "result": null
}
```

**Response (processing):**
```json
{
  "n": 100,
  "status": "processing",
  "result": null
}
```

**Response (done):**
```json
{
  "n": 100,
  "status": "done",
  "result": [2, 3, 5, 7, 11, 13, ..., 541]
}
```

**Response (failed):**
```json
{
  "n": 100,
  "status": "failed",
  "result": null,
  "error": "Error message here"
}
```

### Health Check

**GET /health**

```bash
curl "http://localhost:8000/health"
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Root Endpoint

**GET /**

```bash
curl "http://localhost:8000/"
```

**Response:**
```json
{
  "message": "Welcome to FastAPI",
  "version": "1.0.0",
  "docs": "/docs"
}
```

## How It Works

### Prime Computation

The prime computation logic uses an optimized algorithm that:

1. Checks divisibility only by previously discovered primes (not all numbers)
2. Only checks divisors up to the square root of the candidate number
3. Reuses cached primes from Redis across requests for significant performance gains

**Algorithm:**
```python
def check_prime(number, previous_primes):
    is_prime = True
    limit = int(sqrt(number)) + 1
    for prime in previous_primes:
        if prime <= limit and number % prime == 0:
            is_prime = False
            break
    return is_prime
```

### Caching Strategy

- **Cached Primes Key:** `primes:current` (Redis)
  - Stores a JSON list of all computed primes
  - Persisted periodically during computation and at completion
  - Reused on subsequent requests to avoid recomputation

- **Request State Keys:** `request:{request_id}` (Redis)
  - Stores JSON with fields: `n`, `status`, `result`, optional `error`
  - Status values: `pending`, `processing`, `done`, `failed`

### Request Tracking

Every request gets a unique UUID-based `request_id`. Logs throughout the system (worker, service) include this ID for end-to-end traceability.

## Project Structure

```
API-ASSESSMENT/
├── main.py                      # FastAPI app configuration & initialization
├── celery_app.py               # Celery app & task definitions
├── redis_config.py             # Redis client configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── api/
│   ├── __init__.py
│   ├── health.py              # Health check routes
│   └── tasks.py               # Prime task submission & status routes
├── models/                     # (Pydantic models - currently empty)
├── services/
│   ├── redis_client.py        # Redis client wrapper
│   ├── prime_service.py       # Prime computation with caching
│   └── __init__.py
└── repositories/              # (Data access layer - currently empty)
```

## Notes & Future Improvements

- Worker uses `solo` pool on Windows for stability; change to `prefork` or `threads` in `celery_app.py` on Linux/WSL for concurrency.
- Logs include `request_id` for end-to-end traceability.
- Prime computation is deterministic and cache-aware — subsequent requests for smaller N reuse cache.
- Potential enhancements:
  - Add structured JSON logging (with request_id embedded)
  - Add `/metrics` endpoint for Prometheus monitoring
  - Unit tests for prime service and API
  - Webhook notifications when task completes
  - Task timeout configuration