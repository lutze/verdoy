"""
Health router for operational monitoring endpoints.

This router handles:
- Health check endpoints
- System info
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("")
async def health_check():
    """API health check endpoint."""
    # TODO: Implement health check logic
    return {"status": "ok"}

@router.get("/info")
async def system_info():
    """System info endpoint."""
    # TODO: Implement system info
    return {"info": "Not implemented"} 