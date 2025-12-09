# API-ASSESSMENT: FastAPI + Celery Prime Numbers Service

A FastAPI application that computes the first N prime numbers using Celery background tasks and Redis for caching and state management.

## Overview

This project demonstrates:
- **FastAPI** for HTTP API endpoints
- **Celery** for asynchronous background task processing
- **Redis** for task queue, result storage, and prime number caching
- **Optimized prime computation** with smart caching (reuses previously computed primes)
- **Request tracking** with unique IDs and comprehensive logging

## Quick Start

### 1. Start Redis (Docker recommended)

```powershell
docker run -p 6379:6379 --name redis -d redis:7
```

Or install Redis natively on Windows / use a cloud Redis instance.

### 2. Create & Activate Virtual Environment

Use Python 3.11 or 3.12 (recommended for best compatibility with prebuilt pydantic wheels):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 3. Start Celery Worker

Run in a separate terminal (from project root):

```powershell
celery -A celery_app worker --loglevel=info
```

**Note:** On Windows, the worker uses `solo` pool by default (single-threaded). This avoids multiprocessing issues. On Linux/WSL, you can switch to `prefork` or `threads` pool by editing `celery_app.py`.

### 4. Start FastAPI Application

Run in another terminal:

```powershell
python -m uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`

**API Documentation:**
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

## Troubleshooting

### pip install fails with pydantic-core Rust build error

**Error:**
```
error: subprocess-exited-with-error
× Preparing metadata (pyproject.toml) did not run successfully.
```

**Solution:** Use Python 3.11/3.12 (prebuilt pydantic wheels available):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Or install Rust + MSVC Build Tools to compile from source.

### Celery worker fails with PermissionError on Windows

**Error:**
```
PermissionError(13, 'Access is denied')
```

**Solution:** Already fixed in `celery_app.py` — uses `solo` pool by default. Just run:

```powershell
celery -A celery_app worker --loglevel=info
```

### uvicorn command not found

**Solution:** Run as a module inside the venv:

```powershell
python -m uvicorn main:app --reload
```

### Redis connection refused

**Error:**
```
ConnectionError: Error -2 connecting to localhost:6379. Name or service not known.
```

**Solution:** Verify Redis is running:

```powershell
docker ps  # check if container is running
redis-cli ping  # test connection (if Redis installed natively)
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