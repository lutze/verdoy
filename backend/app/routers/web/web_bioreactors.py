"""
Web-only bioreactors router for /app/bioreactors endpoints.
Handles all HTML-based bioreactor management for web browser clients.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...services.bioreactor_service import BioreactorService
from ...services.organization_service import OrganizationService
from ...schemas.bioreactor import BioreactorCreate, BioreactorUpdate
from ...templates_config import templates

router = APIRouter(prefix="/app/bioreactors", tags=["Web Bioreactors"])

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def list_bioreactors_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """List bioreactors page for web interface (HTML only)."""
    bioreactor_service = BioreactorService(db)
    org_service = OrganizationService(db)
    user_organizations = org_service.get_user_organizations(current_user.id)
    
    # Get bioreactors based on filters
    if organization_id:
        bioreactors_data = bioreactor_service.get_organization_bioreactors(
            organization_id, status, page, 20
        )
        selected_org = org_service.get_by_id(organization_id)
    else:
        bioreactors_data = {
            'bioreactors': [],
            'total_count': 0,
            'page': page,
            'page_size': 20,
            'total_pages': 0
        }
        selected_org = None
        for org in user_organizations:
            org_bioreactors = bioreactor_service.get_organization_bioreactors(
                org.id, status, 1, 1000  # Get all for search
            )
            bioreactors_data['bioreactors'].extend(org_bioreactors['bioreactors'])
            bioreactors_data['total_count'] += org_bioreactors['total_count']
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        bioreactors_data['bioreactors'] = [b for b in bioreactors_data['bioreactors'] if 
                                         search_lower in b.name.lower() or 
                                         (b.description and search_lower in b.description.lower())]
        bioreactors_data['total_count'] = len(bioreactors_data['bioreactors'])
    
    # Get statistics
    stats = {}
    if user_organizations:
        # Get stats for first organization (or selected org)
        target_org = selected_org or user_organizations[0]
        stats = bioreactor_service.get_bioreactor_statistics(target_org.id)
    
    return templates.TemplateResponse("pages/bioreactors/list.html", {
        "request": request,
        "bioreactors": bioreactors_data['bioreactors'],
        "pagination": {
            "page": bioreactors_data['page'],
            "total_pages": bioreactors_data['total_pages'],
            "total_count": bioreactors_data['total_count']
        },
        "organizations": user_organizations,
        "selected_org": selected_org,
        "filters": {
            "status": status,
            "search": search
        },
        "stats": stats,
        "current_user": current_user
    })

@router.get("/enroll", response_class=HTMLResponse, include_in_schema=False)
async def enroll_bioreactor_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    step: int = Query(1, ge=1, le=3),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Bioreactor enrollment page for web interface (HTML only)."""
    org_service = OrganizationService(db)
    user_organizations = org_service.get_user_organizations(current_user.id)
    
    if not user_organizations:
        raise HTTPException(status_code=400, detail="No organizations available")
    
    selected_org = None
    if organization_id:
        selected_org = org_service.get_by_id(organization_id)
        if not selected_org:
            raise HTTPException(status_code=404, detail="Organization not found")
    else:
        selected_org = user_organizations[0]
    
    # Pre-populate form data if available
    form_data = {}
    if step > 1:
        # In a real implementation, you'd get this from session or temporary storage
        form_data = {}
    
    return templates.TemplateResponse("pages/bioreactors/enroll.html", {
        "request": request,
        "step": step,
        "organizations": user_organizations,
        "selected_org": selected_org,
        "form_data": form_data,
        "current_user": current_user
    })

@router.post("/enroll", response_class=HTMLResponse, include_in_schema=False)
async def enroll_bioreactor_post(
    request: Request,
    step: int = Form(1, ge=1, le=3),
    organization_id: UUID = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    bioreactor_type: str = Form("standard"),
    vessel_volume: float = Form(...),
    working_volume: Optional[float] = Form(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Handle bioreactor enrollment form submission."""
    bioreactor_service = BioreactorService(db)
    
    try:
        # For now, handle step 1 only
        if step == 1:
            # Validate basic information
            if vessel_volume <= 0:
                raise HTTPException(status_code=400, detail="Vessel volume must be greater than 0")
            
            if working_volume and working_volume > vessel_volume:
                raise HTTPException(status_code=400, detail="Working volume cannot be greater than vessel volume")
            
            # Store step 1 data (in a real implementation, use session or temporary storage)
            # For now, redirect to step 2
            return RedirectResponse(
                url=f"/app/bioreactors/enroll?organization_id={organization_id}&step=2",
                status_code=302
            )
        
        # Handle other steps
        elif step == 2:
            # Handle hardware configuration
            return RedirectResponse(
                url=f"/app/bioreactors/enroll?organization_id={organization_id}&step=3",
                status_code=302
            )
        
        elif step == 3:
            # Complete enrollment
            # In a real implementation, you'd collect all data and create the bioreactor
            return RedirectResponse(url="/app/bioreactors", status_code=302)
    
    except Exception as e:
        # Return to enrollment page with error
        return templates.TemplateResponse("pages/bioreactors/enroll.html", {
            "request": request,
            "step": step,
            "error": str(e),
            "form_data": {
                "name": name,
                "description": description,
                "location": location,
                "bioreactor_type": bioreactor_type,
                "vessel_volume": vessel_volume,
                "working_volume": working_volume
            },
            "current_user": current_user
        })

@router.get("/{bioreactor_id}", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_detail_page(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Bioreactor detail page for web interface (HTML only)."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        status = bioreactor_service.get_bioreactor_status(bioreactor_id)
        
        return templates.TemplateResponse("pages/bioreactors/detail.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status,
            "current_user": current_user
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Bioreactor not found")

@router.get("/{bioreactor_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_bioreactor_page(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Edit bioreactor page for web interface (HTML only)."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        
        return templates.TemplateResponse("pages/bioreactors/edit.html", {
            "request": request,
            "bioreactor": bioreactor,
            "current_user": current_user
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Bioreactor not found")

@router.post("/{bioreactor_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_bioreactor_post(
    request: Request,
    bioreactor_id: UUID,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    bioreactor_type: str = Form("standard"),
    vessel_volume: float = Form(...),
    working_volume: Optional[float] = Form(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Handle bioreactor edit form submission."""
    bioreactor_service = BioreactorService(db)
    
    try:
        update_data = BioreactorUpdate(
            name=name,
            description=description,
            location=location,
            bioreactor_type=bioreactor_type,
            vessel_volume=vessel_volume,
            working_volume=working_volume
        )
        
        bioreactor = bioreactor_service.update_bioreactor(bioreactor_id, update_data, current_user.id)
        
        return RedirectResponse(url=f"/app/bioreactors/{bioreactor_id}", status_code=302)
    
    except Exception as e:
        # Return to edit page with error
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        return templates.TemplateResponse("pages/bioreactors/edit.html", {
            "request": request,
            "bioreactor": bioreactor,
            "error": str(e),
            "form_data": {
                "name": name,
                "description": description,
                "location": location,
                "bioreactor_type": bioreactor_type,
                "vessel_volume": vessel_volume,
                "working_volume": working_volume
            },
            "current_user": current_user
        })

@router.get("/{bioreactor_id}/control", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_control_page(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Bioreactor control panel page for web interface (HTML only)."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        status = bioreactor_service.get_bioreactor_status(bioreactor_id)
        
        return templates.TemplateResponse("pages/bioreactors/control.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status,
            "current_user": current_user
        })
    except Exception as e:
        raise HTTPException(status_code=404, detail="Bioreactor not found")

@router.post("/{bioreactor_id}/control", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_control_post(
    request: Request,
    bioreactor_id: UUID,
    control_type: str = Form(...),
    parameter: Optional[str] = Form(None),
    value: Optional[float] = Form(None),
    safety_confirmation: bool = Form(False),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Handle bioreactor control form submission."""
    bioreactor_service = BioreactorService(db)
    
    try:
        from ...schemas.bioreactor import BioreactorControlRequest
        
        control_request = BioreactorControlRequest(
            control_type=control_type,
            parameter=parameter,
            value=value,
            safety_confirmation=safety_confirmation
        )
        
        result = bioreactor_service.control_bioreactor(bioreactor_id, control_request, current_user.id)
        
        # Redirect back to control page with success message
        return RedirectResponse(
            url=f"/app/bioreactors/{bioreactor_id}/control?success={result['message']}",
            status_code=302
        )
    
    except Exception as e:
        # Redirect back to control page with error
        return RedirectResponse(
            url=f"/app/bioreactors/{bioreactor_id}/control?error={str(e)}",
            status_code=302
        )

@router.get("/{bioreactor_id}/status", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_status_partial(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for bioreactor status updates."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        status = bioreactor_service.get_bioreactor_status(bioreactor_id)
        
        return templates.TemplateResponse("partials/bioreactor_status.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status
        })
    except Exception as e:
        return templates.TemplateResponse("partials/bioreactor_status.html", {
            "request": request,
            "error": str(e)
        })

@router.post("/{bioreactor_id}/archive", response_class=HTMLResponse, include_in_schema=False)
async def archive_bioreactor_post(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Handle bioreactor archive form submission."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.archive_bioreactor(bioreactor_id, current_user.id)
        return RedirectResponse(url="/app/bioreactors?archived=true", status_code=302)
    
    except Exception as e:
        return RedirectResponse(
            url=f"/app/bioreactors/{bioreactor_id}?error={str(e)}",
            status_code=302
        ) 