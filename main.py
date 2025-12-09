import uvicorn
from fastapi import FastAPI
from api import health_router
from api import tasks_router

# Initialize FastAPI app
app = FastAPI(
    title="My FastAPI Application",
    description="Application to calculate N prime numbers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Register routers
app.include_router(health_router)
app.include_router(tasks_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
