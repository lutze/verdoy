"""
Dashboard router for user dashboard and overview pages.

This router handles:
- User dashboard with organization overview
- Summary statistics and activity feeds
- Quick access to key features
- Real-time data updates via HTMX
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from ..dependencies import get_db, get_current_user
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..templates_config import templates

router = APIRouter(tags=["Dashboard"])

def accepts_json(request: Request) -> bool:
    """Check if client prefers JSON responses"""
    accept_header = request.headers.get("accept", "")
    return (
        "application/json" in accept_header or
        "application/ld+json" in accept_header or
        request.url.path.startswith("/api/")
    )

# ============================================================================
# HTML PAGES (GET ROUTES)
# ============================================================================

@router.get("/app/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Display user dashboard for web browsers."""
    # TODO: Implement actual data fetching from services
    # For now, provide mock data for development
    
    # Mock dashboard data
    dashboard_data = {
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
                "online_bioreactors": 2,
                "recent_activity": [
                    {"type": "experiment_started", "message": "Experiment 'pH Optimization' started", "time": "2 hours ago"},
                    {"type": "bioreactor_online", "message": "Bioreactor BR-001 came online", "time": "4 hours ago"},
                    {"type": "data_collected", "message": "Temperature data collected from BR-002", "time": "6 hours ago"}
                ]
            },
            {
                "id": "2", 
                "name": "University Lab",
                "description": "Academic research projects",
                "member_count": 12,
                "active_experiments": 1,
                "online_bioreactors": 0,
                "recent_activity": [
                    {"type": "experiment_completed", "message": "Experiment 'Growth Rate Study' completed", "time": "1 day ago"}
                ]
            }
        ],
        "summary_stats": {
            "total_organizations": 2,
            "total_experiments": 4,
            "total_bioreactors": 3,
            "online_bioreactors": 2,
            "data_points_today": 15420
        },
        "recent_activity": [
            {"type": "experiment_started", "message": "Experiment 'pH Optimization' started", "time": "2 hours ago", "org": "Acme Research Lab"},
            {"type": "bioreactor_online", "message": "Bioreactor BR-001 came online", "time": "4 hours ago", "org": "Acme Research Lab"},
            {"type": "data_collected", "message": "Temperature data collected from BR-002", "time": "6 hours ago", "org": "Acme Research Lab"},
            {"type": "experiment_completed", "message": "Experiment 'Growth Rate Study' completed", "time": "1 day ago", "org": "University Lab"}
        ]
    }
    
    return templates.TemplateResponse("pages/dashboard/index.html", {
        "request": request,
        "dashboard": dashboard_data
    })

@router.get("/app/dashboard/activity", response_class=HTMLResponse, include_in_schema=False)
async def activity_feed(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for activity feed updates."""
    # TODO: Implement real activity feed with pagination
    # For now, return mock activity data
    
    activities = [
        {"type": "experiment_started", "message": "Experiment 'pH Optimization' started", "time": "2 hours ago", "org": "Acme Research Lab"},
        {"type": "bioreactor_online", "message": "Bioreactor BR-001 came online", "time": "4 hours ago", "org": "Acme Research Lab"},
        {"type": "data_collected", "message": "Temperature data collected from BR-002", "time": "6 hours ago", "org": "Acme Research Lab"},
        {"type": "experiment_completed", "message": "Experiment 'Growth Rate Study' completed", "time": "1 day ago", "org": "University Lab"},
        {"type": "user_joined", "message": "Dr. Smith joined University Lab", "time": "2 days ago", "org": "University Lab"},
        {"type": "bioreactor_enrolled", "message": "New bioreactor BR-003 enrolled", "time": "3 days ago", "org": "Acme Research Lab"}
    ]
    
    return templates.TemplateResponse("partials/activity_feed.html", {
        "request": request,
        "activities": activities
    })

@router.get("/app/dashboard/stats", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_stats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for dashboard statistics updates."""
    # TODO: Implement real-time statistics
    # For now, return mock stats
    
    stats = {
        "total_organizations": 2,
        "total_experiments": 4,
        "total_bioreactors": 3,
        "online_bioreactors": 2,
        "data_points_today": 15420,
        "active_experiments": 4,
        "completed_experiments": 12
    }
    
    return templates.TemplateResponse("partials/dashboard_stats.html", {
        "request": request,
        "stats": stats
    })

# ============================================================================
# JSON API ENDPOINTS (for programmatic clients)
# ============================================================================

@router.get("/api/v1/dashboard")
async def get_dashboard_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard data for programmatic clients."""
    # TODO: Implement actual data fetching
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