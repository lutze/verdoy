"""
Organizations router for multi-tenant organization management.

This router handles:
- Organization CRUD operations
- Member management and invitations
- Organization settings and statistics
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ..dependencies import get_db, get_current_user
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..services.organization_service import OrganizationService
from ..schemas.organization import OrganizationCreate, OrganizationUpdate
from ..templates_config import templates

router = APIRouter(tags=["Organizations"])

def accepts_json(request: Request) -> bool:
    """Check if client accepts JSON responses."""
    accept_header = request.headers.get("accept", "")
    return (
        "application/json" in accept_header or
        "application/ld+json" in accept_header or
        request.url.path.startswith("/api/")
    )

@router.get("/app/admin/organization/", response_class=HTMLResponse, include_in_schema=False)
async def list_organizations_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organizations page for web interface."""
    if accepts_json(request):
        return await list_organizations_api(request, current_user, db)
    
    # Get user's organizations
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

@router.get("/api/v1/organizations", response_model=BaseResponse)
async def list_organizations_api(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List organizations for API clients."""
    org_service = OrganizationService(db)
    organizations = org_service.get_user_organizations(current_user.id)
    
    return BaseResponse(
        success=True,
        data={"organizations": organizations},
        message="Organizations retrieved successfully"
    )

@router.get("/app/admin/organization/create", response_class=HTMLResponse, include_in_schema=False)
async def create_organization_page(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Create organization page for web interface."""
    return templates.TemplateResponse(
        "pages/organizations/create.html",
        {
            "request": request,
            "user": current_user,
            "page_title": "Create Organization"
        }
    )

@router.post("/app/admin/organization/create", response_class=HTMLResponse, include_in_schema=False)
async def create_organization_page_submit(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    organization_type: str = Form("small_business"),
    website: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    timezone: str = Form("UTC"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create organization form submission for web interface."""
    if accepts_json(request):
        return await create_organization_api(request, current_user, db)
    
    try:
        # Create organization data
        org_data = OrganizationCreate(
            name=name,
            description=description,
            organization_type=organization_type,
            website=website,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            timezone=timezone
        )
        
        # Create organization
        org_service = OrganizationService(db)
        organization = org_service.create_organization(org_data, current_user.id)
        
        # Redirect to organization detail page
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=f"/app/admin/organization/{organization.id}",
            status_code=303
        )
        
    except Exception as e:
        # Return form with error
        return templates.TemplateResponse(
            "pages/organizations/create.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "Create Organization",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "description": description,
                    "organization_type": organization_type,
                    "website": website,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "address": address,
                    "city": city,
                    "state": state,
                    "country": country,
                    "postal_code": postal_code,
                    "timezone": timezone
                }
            }
        )

@router.post("/api/v1/organizations", response_model=BaseResponse)
async def create_organization_api(
    request: Request,
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create organization for API clients."""
    org_service = OrganizationService(db)
    organization = org_service.create_organization(org_data, current_user.id)
    
    return BaseResponse(
        success=True,
        data={"organization": organization},
        message="Organization created successfully"
    )

@router.get("/app/admin/organization/{org_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_organization_page(
    request: Request,
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Organization detail page for web interface."""
    if accepts_json(request):
        return await get_organization_api(request, org_id, current_user, db)
    
    try:
        org_service = OrganizationService(db)
        organization = org_service.get_by_id_or_raise(org_id)
        
        # Get organization members
        members = org_service.get_organization_users(org_id)
        
        # Get organization statistics
        stats = org_service.get_organization_statistics()
        
        return templates.TemplateResponse(
            "pages/organizations/detail.html",
            {
                "request": request,
                "user": current_user,
                "organization": organization,
                "members": members,
                "stats": stats,
                "page_title": f"Organization: {organization.name}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Organization not found")

@router.get("/api/v1/organizations/{org_id}", response_model=BaseResponse)
async def get_organization_api(
    request: Request,
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization details for API clients."""
    org_service = OrganizationService(db)
    organization = org_service.get_by_id_or_raise(org_id)
    
    return BaseResponse(
        success=True,
        data={"organization": organization},
        message="Organization retrieved successfully"
    ) 