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
            "page_title": "Organizations"
        }
    )

# TODO: Add create, detail, edit, and other /app/admin/organization endpoints as needed (HTML only). 