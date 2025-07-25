"""
Web-only projects router for /app/projects endpoints.
Handles all HTML-based project management for web browser clients.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...services.project_service import ProjectService
from ...services.organization_service import OrganizationService
from ...templates_config import templates

router = APIRouter(prefix="/app/projects", tags=["Web Projects"])

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def list_projects_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """List projects page for web interface (HTML only)."""
    project_service = ProjectService(db)
    org_service = OrganizationService(db)
    user_organizations = org_service.get_user_organizations(current_user.id)
    if organization_id:
        projects = project_service.get_projects_by_organization(organization_id, status)
        selected_org = org_service.get_by_id(organization_id)
    else:
        projects = []
        selected_org = None
        for org in user_organizations:
            org_projects = project_service.get_projects_by_organization(org.id, status)
            projects.extend(org_projects)
    stats = project_service.get_project_statistics()
    return templates.TemplateResponse(
        "pages/projects/list.html",
        {
            "request": request,
            "user": current_user,
            "projects": projects,
            "organizations": user_organizations,
            "selected_organization": selected_org,
            "selected_status": status,
            "stats": stats,
            "page_title": "Projects"
        }
    )

# TODO: Add create, detail, edit, and other /app/projects endpoints as needed (HTML only). 