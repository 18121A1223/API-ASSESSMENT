# How to Run the Application

## Step 1: Setup Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## Step 2: Start Docker Compose Stack

This starts Grafana, Prometheus, VictoriaMetrics, Redis, and Redis Exporter.

```powershell
docker-compose -f docker-compose.monitoring.yml up -d
```

Wait 60 seconds for services to stabilize.

## Step 3: Start FastAPI (Open Terminal 1)

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn main:app --reload
```

FastAPI will be running at http://localhost:8000

## Step 4: Start Celery Worker (Open Terminal 2)

```powershell
.\.venv\Scripts\Activate.ps1
celery -A celery_app worker --loglevel=info
```

Celery worker will listen for tasks.

## Step 5: Access the Services

Open these in your browser:

| Service | URL | Login |
|---------|-----|-------|
| **Grafana Dashboard** | http://localhost:3000 | admin / admin |
| **Prometheus Metrics** | http://localhost:9090 | - |
| **VictoriaMetrics** | http://localhost:8428 | - |
| **API Documentation** | http://localhost:8000/docs | - |

## Service URLs Reference

### 📊 All Available Services

| Service | URL | Purpose |
|---------|-----|---------|
| **FastAPI App** | http://localhost:8000 | Main application endpoints |
| **FastAPI Docs (Swagger)** | http://localhost:8000/docs | Interactive API documentation |
| **FastAPI Health Check** | http://localhost:8000/health | Service health status |
| **Grafana** | http://localhost:3000 | Dashboards and visualization |
| **Prometheus** | http://localhost:9090 | Metrics collection and querying |
| **Prometheus Targets** | http://localhost:9090/targets | View scrape targets and status |
| **VictoriaMetrics** | http://localhost:8428 | Long-term metrics storage |
| **Celery Worker Metrics** | http://localhost:8001/metrics | Celery task metrics (when running in Docker) |
| **Redis Exporter** | http://localhost:9121/metrics | Redis instance metrics |
| **Prometheus** | http://localhost:9090 | Metrics queries and graphs |
| **Prometheus Targets** | http://localhost:9090/targets | View scrape target status |
| **VictoriaMetrics** | http://localhost:8428 | Time-series database API |
| **Redis Metrics Exporter** | http://localhost:9121/metrics | Redis metrics in Prometheus format |

### 🔑 Credentials

- **Grafana**: Username: `admin` / Password: `admin`
- **Redis**: No authentication (local only)

### 📝 Common API Test Commands

**Submit a task:**
```powershell
$body = @{ n = 100 } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/tasks" `
  -Method POST -Body $body -ContentType "application/json"
```

**Check task status:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/tasks/{request_id}" -Method GET
```

**Get metrics summary:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/summary" -Method GET
```

**View all metrics:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/metrics/all" -Method GET
```

## Grafana Dashboards

Once logged in to Grafana (admin/admin), you'll see pre-configured dashboards:

1. **Prime API Metrics** - Task submissions, completions, cache hits, processing time
2. **Redis Metrics** - Redis memory usage, connections, operations
3. **System Metrics** - CPU, memory, disk usage

### Monitoring Checklist

✅ Verify FastAPI is healthy: GET http://localhost:8000/health (should return 200)
✅ Check Prometheus targets: http://localhost:9090/targets (all should show green)
✅ View Grafana dashboards: http://localhost:3000 (login admin/admin)
✅ Submit test task and monitor metrics

## Step 6: Submit a Test Task (Terminal 3)

```powershell
# Submit a task
$response = curl -X POST http://localhost:8000/tasks `
  -H "Content-Type: application/json" `
  -d '{"n":100}' -UseBasicParsing | ConvertFrom-Json

$requestId = $response.request_id
Write-Host "Task ID: $requestId"

# Check status
curl http://localhost:8000/tasks/$requestId
```

---

## Monitoring in Grafana

1. Open http://localhost:3000
2. Login with admin / admin
3. Go to **Dashboards** (left sidebar)
4. Select **Prime API Metrics** or **Redis Metrics**
5. Watch real-time data update as tasks run

---

## Query Metrics via API

```powershell
# Get summary
curl http://localhost:8000/api/metrics/summary | ConvertFrom-Json

# Get cache statistics
curl http://localhost:8000/api/metrics/cache-stats | ConvertFrom-Json

# Get task statistics
curl http://localhost:8000/api/metrics/task-stats | ConvertFrom-Json

# Get Redis statistics
curl http://localhost:8000/api/metrics/redis-stats | ConvertFrom-Json

# Get all metrics
curl http://localhost:8000/api/metrics/all | ConvertFrom-Json
```

---

## Useful Commands

### Check service status
```powershell
docker-compose -f docker-compose.monitoring.yml ps
Get-Job
```

### View Docker logs
```powershell
docker-compose -f docker-compose.monitoring.yml logs -f
```

### View specific service logs
```powershell
docker-compose -f docker-compose.monitoring.yml logs -f grafana
docker-compose -f docker-compose.monitoring.yml logs -f prometheus
```

### Check Prometheus targets
```
http://localhost:9090/targets
```
All 4 targets should be UP (green):
- fastapi:8000/metrics
- celery:8001
- redis-exporter:9121
- victoriametrics:8428

### Clear Redis cache
```powershell
redis-cli FLUSHDB
```

### Check active Celery tasks
```powershell
celery -A celery_app inspect active
```

---

## Stop Everything

```powershell
# Stop Docker Compose services
docker-compose -f docker-compose.monitoring.yml down

# Stop background jobs (FastAPI, Celery)
Get-Job | Stop-Job
Get-Job | Remove-Job
```

---

## Notes

- **FastAPI** runs on port 8000
- **Grafana** runs on port 3000
- **Prometheus** runs on port 9090
- **VictoriaMetrics** runs on port 8428
- **Redis** runs on port 6379
- **Celery** uses Redis as broker
- Windows Celery uses `solo` pool (single-threaded)
