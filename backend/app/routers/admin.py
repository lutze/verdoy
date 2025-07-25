"""
Admin router for platform management endpoints.

This router handles:
- User and device listing for admins
- Platform statistics
- Administrative actions
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from ..models.user import User

router = APIRouter(tags=["Admin"])

@router.get("/users")
async def list_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    # TODO: Implement admin user listing
    users = []  # Replace with actual user list
    return {"users": users, "size": len(users)}

@router.get("/devices")
async def list_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all devices (admin only)."""
    # TODO: Implement admin device listing
    devices = []  # Replace with actual device list
    return {"devices": devices, "size": len(devices)}

@router.get("/stats")
async def get_platform_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get platform statistics (admin only)."""
    # TODO: Implement platform stats
    return {"stats": "Not implemented"} 