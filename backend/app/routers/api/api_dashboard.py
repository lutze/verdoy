"""
API-only dashboard router for /api/v1/dashboard endpoints.
Handles all JSON-based dashboard data for programmatic clients.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from ...dependencies import get_db, get_api_user
from ...models.user import User

router = APIRouter(prefix="/api/v1/dashboard", tags=["API Dashboard"])

@router.get("", summary="Get dashboard data (API)")
async def get_dashboard_data(
    request: Request,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """Get dashboard data for programmatic clients (JSON only)."""
    # TODO: Implement actual data fetching from services
    # For now, return mock data structure
    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.entity.name if current_user.entity else "Unknown User",
            "is_active": current_user.is_active
        },
        "organizations": [
            {
                "id": "1",
                "name": "Acme Research Lab",
                "description": "Primary research organization",
                "member_count": 5,
                "active_experiments": 3,
                "online_bioreactors": 2
            },
            {
                "id": "2",
                "name": "University Lab",
                "description": "Academic research projects",
                "member_count": 12,
                "active_experiments": 1,
                "online_bioreactors": 0
            }
        ],
        "summary_stats": {
            "total_organizations": 2,
            "total_experiments": 4,
            "total_bioreactors": 3,
            "online_bioreactors": 2,
            "data_points_today": 15420
        }
    } 