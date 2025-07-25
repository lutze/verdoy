"""
Web-only organizations router for /app/admin/organization endpoints.
Handles all HTML-based organization management for web browser clients.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...services.organization_service import OrganizationService
from ...templates_config import templates

router = APIRouter(prefix="/app/admin/organization", tags=["Web Organizations"])

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def list_organizations_page(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """List organizations page for web interface (HTML only)."""
    org_service = OrganizationService(db)
    organizations = org_service.get_user_organizations(current_user.id)
    return templates.TemplateResponse(
        "pages/organizations/list.html",
        {
            "request": request,
            "user": current_user,
            "organizations": organizations,
            "page_title": "Organizations",
            "current_user": current_user
        }
    )

@router.get("/{organization_id}", response_class=HTMLResponse, include_in_schema=False)
async def organization_detail_page(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    org_service = OrganizationService(db)
    organization = org_service.get_by_id(organization_id)
    stats = org_service.get_organization_stats(organization_id)
    return templates.TemplateResponse(
        "pages/organizations/detail.html",
        {
            "request": request,
            "organization": organization,
            "stats": stats,
            "current_user": current_user,
            "page_title": organization.name if organization else "Organization Detail"
        }
    )

@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def organization_create_page(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        "pages/organizations/create.html",
        {
            "request": request,
            "current_user": current_user,
            "page_title": "Create Organization"
        }
    )

@router.get("/{organization_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def organization_edit_page(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    org_service = OrganizationService(db)
    organization = org_service.get_by_id(organization_id)
    return templates.TemplateResponse(
        "pages/organizations/edit.html",
        {
            "request": request,
            "organization": organization,
            "current_user": current_user,
            "page_title": f"Edit {organization.name if organization else 'Organization'}"
        }
    ) 