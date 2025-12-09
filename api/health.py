from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "wealthy"}

@router.get("/")
def read_root():
    """Root endpoint"""
    return {
        "message": "Welcome to FastAPI",
        "version": "1.0.0",
        "docs": "/docs"
    }
