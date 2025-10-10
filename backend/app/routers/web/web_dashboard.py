"""
Web-only dashboard router for /app/dashboard endpoints.
Handles all HTML-based dashboard pages for web browser clients.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...services.organization_service_entity import OrganizationServiceEntity
from ...templates_config import templates

router = APIRouter(prefix="/app/dashboard", tags=["Web Dashboard"])

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Display user dashboard for web browsers."""
    # Get user's organizations
    org_service = OrganizationServiceEntity(db)
    user_organizations = org_service.get_user_organizations(current_user.id)
    
    # Convert organizations to dashboard format
    organizations_data = []
    total_experiments = 0
    total_bioreactors = 0
    online_bioreactors = 0
    
    for org in user_organizations:
        # Get organization stats
        stats = org_service.get_organization_stats(org.id)
        
        org_data = {
            "id": str(org.id),  # Use actual UUID as string
            "name": org.name,
            "description": org.description or "Research organization",
            "member_count": stats.get('member_count', 0),
            "active_experiments": stats.get('project_count', 0),  # Using project_count as placeholder for experiments
            "online_bioreactors": stats.get('online_devices', 0),  # Using online_devices as placeholder for bioreactors
            "recent_activity": [
                {"type": "organization_created", "message": f"Organization '{org.name}' created", "time": "Recently"}
            ]
        }
        organizations_data.append(org_data)
        
        # Aggregate stats
        total_experiments += org_data["active_experiments"]
        total_bioreactors += stats.get('device_count', 0)  # Using device_count as placeholder for bioreactors
        online_bioreactors += org_data["online_bioreactors"]
    
    # If no organizations, provide a message to create one
    if not organizations_data:
        organizations_data = []
        # Note: We don't create a fake organization with "default" ID anymore
        # Instead, we'll show an empty state in the template
    
    dashboard_data = {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "name": current_user.name,
            "is_active": current_user.is_active
        },
        "organizations": organizations_data,
        "summary_stats": {
            "total_organizations": len(organizations_data),
            "total_experiments": total_experiments,
            "total_bioreactors": total_bioreactors,
            "online_bioreactors": online_bioreactors,
            "data_points_today": 0  # TODO: Implement actual data point counting
        },
        "recent_activity": [
            {"type": "welcome", "message": f"Welcome back, {current_user.name or current_user.email}!", "time": "Just now", "org": "System"}
        ]
    }
    
    return templates.TemplateResponse("pages/dashboard/index.html", {
        "request": request,
        "dashboard": dashboard_data,
        "current_user": current_user
    })

@router.get("/activity", response_class=HTMLResponse, include_in_schema=False)
async def activity_feed(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for activity feed updates."""
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

@router.get("/stats", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_stats(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for dashboard statistics updates."""
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