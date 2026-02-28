"""
System router for API health and system metrics.

This router handles:
- API health check
- System metrics
- Version information
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..dependencies import get_db

router = APIRouter(tags=["System"])

@router.get("/health")
async def health_check():
    """API health check endpoint."""
    return {"status": "ok"}

@router.get("/metrics")
async def get_metrics():
    """System metrics endpoint."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})

@router.get("/version")
async def get_version():
    """API version information."""
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})
