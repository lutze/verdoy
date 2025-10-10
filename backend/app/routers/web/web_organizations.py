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
from ...services.organization_service_entity import OrganizationServiceEntity
from ...templates_config import templates

router = APIRouter(prefix="/app/admin/organization", tags=["Web Organizations"])

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def list_organizations_page(
    request: Request,
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    organization_type: Optional[str] = Query(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """List organizations page for web interface (HTML only)."""
    org_service = OrganizationServiceEntity(db)
    organizations = org_service.get_all_organizations()
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        organizations = [org for org in organizations if 
                       search_lower in org.name.lower() or 
                       (org.description and search_lower in org.description.lower())]
    
    # Apply status filter if provided
    if status:
        organizations = [org for org in organizations if org.status == status]
    
    # Apply organization type filter if provided
    if organization_type:
        organizations = [org for org in organizations if org.organization_type == organization_type]
    
    return templates.TemplateResponse(
        "pages/organizations/list.html",
        {
            "request": request,
            "user": current_user,
            "organizations": organizations,
            "selected_search": search,
            "selected_status": status,
            "selected_type": organization_type,
            "page_title": "Organizations",
            "current_user": current_user
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

@router.get("/{organization_id}", response_class=HTMLResponse, include_in_schema=False)
async def organization_detail_page(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    org_service = OrganizationServiceEntity(db)
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

@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
async def organization_create(
    request: Request,
    name: str = Form(...),
    organization_type: str = Form("small_business"),
    description: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    timezone: str = Form("UTC"),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    org_service = OrganizationServiceEntity(db)
    try:
        # Create OrganizationCreate object from form data
        from ...schemas.organization import OrganizationCreate
        org_data = OrganizationCreate(
            name=name,
            organization_type=organization_type,
            description=description,
            contact_email=contact_email,
            contact_phone=contact_phone,
            website=website,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            timezone=timezone
        )
        
        organization = org_service.create_organization(org_data, created_by=current_user.id)
        return RedirectResponse(url=f"/app/admin/organization/{organization.id}", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "pages/organizations/create.html",
            {
                "request": request,
                "current_user": current_user,
                "page_title": "Create Organization",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "organization_type": organization_type,
                    "description": description,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "website": website,
                    "address": address,
                    "city": city,
                    "state": state,
                    "country": country,
                    "postal_code": postal_code,
                    "timezone": timezone
                }
            }
        )

@router.get("/{organization_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def organization_edit_page(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    org_service = OrganizationServiceEntity(db)
    organization = org_service.get_by_id(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return templates.TemplateResponse(
        "pages/organizations/edit.html",
        {
            "request": request,
            "organization": organization,
            "current_user": current_user,
            "page_title": f"Edit {organization.name}"
        }
    )

@router.post("/{organization_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def organization_update(
    request: Request,
    organization_id: UUID,
    name: str = Form(...),
    organization_type: str = Form("small_business"),
    description: Optional[str] = Form(None),
    contact_email: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    website: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    state: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    timezone: str = Form("UTC"),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Update an existing organization."""
    org_service = OrganizationServiceEntity(db)
    organization = org_service.get_by_id(organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    try:
        updated_organization = org_service.update_organization(
            organization_id=organization_id,
            name=name,
            organization_type=organization_type,
            description=description,
            contact_email=contact_email,
            contact_phone=contact_phone,
            website=website,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            timezone=timezone
        )
        return RedirectResponse(url=f"/app/admin/organization/{organization_id}", status_code=302)
    except Exception as e:
        return templates.TemplateResponse(
            "pages/organizations/edit.html",
            {
                "request": request,
                "organization": organization,
                "current_user": current_user,
                "page_title": f"Edit {organization.name}",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "organization_type": organization_type,
                    "description": description,
                    "contact_email": contact_email,
                    "contact_phone": contact_phone,
                    "website": website,
                    "address": address,
                    "city": city,
                    "state": state,
                    "country": country,
                    "postal_code": postal_code,
                    "timezone": timezone
                }
            }
        ) 