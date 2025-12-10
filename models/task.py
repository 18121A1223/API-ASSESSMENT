from pydantic import BaseModel, Field
from typing import Optional, Any


class CreateTaskRequest(BaseModel):
    """Request model for creating a prime computation task"""
    n: int = Field(..., gt=0, description="Number of primes to compute")


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    n: int
    status: str
    result: Optional[list] = None
    error: Optional[str] = None
