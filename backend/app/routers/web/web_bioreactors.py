"""
Web-only bioreactors router for /app/bioreactors endpoints.
Handles all HTML-based bioreactor management for web browser clients.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...models.bioreactor import Bioreactor
from ...services.bioreactor_service import BioreactorService
from ...services.organization_service import OrganizationService
from ...schemas.bioreactor import BioreactorCreate, BioreactorUpdate, SensorConfig, ActuatorConfig
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
    step: int = Query(1, ge=1, le=4),
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
        # Extract form data from URL parameters
        form_data = {
            "name": request.query_params.get("name"),
            "description": request.query_params.get("description"),
            "location": request.query_params.get("location"),
            "bioreactor_type": request.query_params.get("bioreactor_type", "stirred_tank"),
            "vessel_volume": request.query_params.get("vessel_volume"),
            "working_volume": request.query_params.get("working_volume"),
            "sensors": request.query_params.getlist("sensors") if request.query_params.get("sensors") else [],
            "actuators": request.query_params.getlist("actuators") if request.query_params.get("actuators") else [],
            "firmware_version": request.query_params.get("firmware_version", "1.0.0"),
            "hardware_model": request.query_params.get("hardware_model"),
            "mac_address": request.query_params.get("mac_address"),
            "reading_interval": request.query_params.get("reading_interval", "300")
        }
        
        # Convert numeric values
        if form_data["vessel_volume"]:
            try:
                form_data["vessel_volume"] = float(form_data["vessel_volume"])
            except ValueError:
                form_data["vessel_volume"] = None
        
        if form_data["working_volume"]:
            try:
                form_data["working_volume"] = float(form_data["working_volume"])
            except ValueError:
                form_data["working_volume"] = None
    
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
    step: int = Form(1, ge=1, le=4),
    organization_id: UUID = Form(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    bioreactor_type: Optional[str] = Form("stirred_tank"),
    vessel_volume: Optional[float] = Form(None),
    working_volume: Optional[str] = Form(None),
    sensors: Optional[list] = Form(None),
    actuators: Optional[list] = Form(None),
    firmware_version: Optional[str] = Form("1.0.0"),
    hardware_model: Optional[str] = Form(None),
    mac_address: Optional[str] = Form(None),
    reading_interval: Optional[int] = Form(300),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Handle bioreactor enrollment form submission."""
    bioreactor_service = BioreactorService(db)
    
    try:
        # Handle working_volume - convert string to float, handle empty string
        working_volume_float = None
        if working_volume and working_volume.strip():
            try:
                working_volume_float = float(working_volume)
            except ValueError:
                raise HTTPException(status_code=400, detail="Working volume must be a valid number")
        
        if step == 1:
            # Validate step 1 data
            if not name:
                raise HTTPException(status_code=400, detail="Name is required")
            if not vessel_volume or vessel_volume <= 0:
                raise HTTPException(status_code=400, detail="Vessel volume must be greater than 0")
            
            if working_volume_float and working_volume_float > vessel_volume:
                raise HTTPException(status_code=400, detail="Working volume cannot be greater than vessel volume")
            
            # Store step 1 data and redirect to step 2
            form_data = {
                "name": name,
                "description": description,
                "location": location,
                "bioreactor_type": bioreactor_type,
                "vessel_volume": vessel_volume,
                "working_volume": working_volume_float
            }
            
            # In a real implementation, you'd store this in session or temporary storage
            # For now, we'll pass it as URL parameters (not ideal but works for demo)
            params = f"organization_id={organization_id}&step=2"
            for key, value in form_data.items():
                if value is not None:
                    params += f"&{key}={value}"
            
            return RedirectResponse(url=f"/app/bioreactors/enroll?{params}", status_code=302)
        
        elif step == 2:
            # Handle hardware configuration step
            # For now, just redirect to step 3 with the data
            form_data = {
                "name": name,
                "description": description,
                "location": location,
                "bioreactor_type": bioreactor_type,
                "vessel_volume": vessel_volume,
                "working_volume": working_volume_float,
                "sensors": sensors,
                "actuators": actuators
            }
            
            params = f"organization_id={organization_id}&step=3"
            for key, value in form_data.items():
                if value is not None:
                    if isinstance(value, list):
                        for item in value:
                            params += f"&{key}={item}"
                    else:
                        params += f"&{key}={value}"
            
            return RedirectResponse(url=f"/app/bioreactors/enroll?{params}", status_code=302)
        
        elif step == 3:
            # Handle device configuration step
            form_data = {
                "name": name,
                "description": description,
                "location": location,
                "bioreactor_type": bioreactor_type,
                "vessel_volume": vessel_volume,
                "working_volume": working_volume_float,
                "sensors": sensors,
                "actuators": actuators,
                "firmware_version": firmware_version,
                "hardware_model": hardware_model,
                "mac_address": mac_address,
                "reading_interval": reading_interval
            }
            
            params = f"organization_id={organization_id}&step=4"
            for key, value in form_data.items():
                if value is not None:
                    if isinstance(value, list):
                        for item in value:
                            params += f"&{key}={item}"
                    else:
                        params += f"&{key}={value}"
            
            return RedirectResponse(url=f"/app/bioreactors/enroll?{params}", status_code=302)
        
        elif step == 4:
            # Complete enrollment
            if not name or not vessel_volume:
                raise HTTPException(status_code=400, detail="Missing required fields")
            
            try:
                # Create bioreactor with complete data
                bioreactor = Bioreactor(
                    name=name,
                    description=description,
                    organization_id=organization_id,
                    entity_type='device.bioreactor',
                    status='offline'
                )
                
                # Set location in properties if provided
                if location:
                    bioreactor.set_property('location', location)
                
                # Set bioreactor-specific properties
                bioreactor.set_bioreactor_type(bioreactor_type or "stirred_tank")
                bioreactor.set_vessel_volume(vessel_volume)
                
                # Set working volume - use 70% of vessel volume as default if not provided
                if working_volume_float:
                    bioreactor.set_working_volume(working_volume_float)
                else:
                    # Default to 70% of vessel volume
                    default_working_volume = vessel_volume * 0.7
                    bioreactor.set_working_volume(default_working_volume)
                
                # Set hardware configuration
                hardware_config = {
                    'model': hardware_model or 'Generic Bioreactor',
                    'macAddress': mac_address or '00:00:00:00:00:00',
                    'sensors': [{"type": sensor, "unit": "standard", "status": "active"} for sensor in (sensors or [])],
                    'actuators': [{"type": actuator, "unit": "standard", "status": "active"} for actuator in (actuators or [])]
                }
                bioreactor.set_property('hardware', hardware_config)
                
                # Set firmware configuration
                firmware_config = {
                    'version': firmware_version or '1.0.0',
                    'lastUpdate': datetime.utcnow().isoformat()
                }
                bioreactor.set_property('firmware', firmware_config)
                
                # Set reading interval
                bioreactor.set_property('reading_interval', reading_interval or 300)
                
                # Save to database
                db.add(bioreactor)
                db.commit()
                db.refresh(bioreactor)
                
                return RedirectResponse(url="/app/bioreactors", status_code=302)
                
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Failed to create bioreactor: {str(e)}")
    
    except Exception as e:
        # Return to enrollment page with error
        form_data = {
            "name": name,
            "description": description,
            "location": location,
            "bioreactor_type": bioreactor_type,
            "vessel_volume": vessel_volume,
            "working_volume": working_volume_float,
            "sensors": sensors,
            "actuators": actuators,
            "firmware_version": firmware_version,
            "hardware_model": hardware_model,
            "mac_address": mac_address,
            "reading_interval": reading_interval
        }
        
        # Get organization data for error context
        org_service = OrganizationService(db)
        user_organizations = org_service.get_user_organizations(current_user.id)
        selected_org = None
        if organization_id:
            selected_org = org_service.get_by_id(organization_id)
        elif user_organizations:
            selected_org = user_organizations[0]
        
        return templates.TemplateResponse("pages/bioreactors/enroll.html", {
            "request": request,
            "step": step,
            "error": str(e),
            "form_data": form_data,
            "organizations": user_organizations,
            "selected_org": selected_org,
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
        print(f"Found bioreactor: {bioreactor.id} - {bioreactor.name}")
        
        try:
            status = bioreactor_service.get_bioreactor_status(bioreactor_id)
            print(f"Got status for bioreactor: {status}")
        except Exception as status_error:
            print(f"Error getting status: {status_error}")
            # Create a basic status if the full status fails
            status = {
                "id": bioreactor.id,
                "name": bioreactor.name,
                "status": "offline",
                "control_mode": "manual",
                "is_operational": False,
                "is_running_experiment": False
            }
        
        return templates.TemplateResponse("pages/bioreactors/detail.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status,
            "current_user": current_user
        })
    except Exception as e:
        print(f"Error in bioreactor detail page: {e}")
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

@router.get("/{bioreactor_id}/data", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_data_partial(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for bioreactor sensor data updates."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        status = bioreactor_service.get_bioreactor_status(bioreactor_id)
        
        return templates.TemplateResponse("partials/bioreactor_data.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status
        })
    except Exception as e:
        return templates.TemplateResponse("partials/bioreactor_data.html", {
            "request": request,
            "error": str(e)
        })

@router.get("/{bioreactor_id}/control-panel", response_class=HTMLResponse, include_in_schema=False)
async def bioreactor_control_panel_partial(
    request: Request,
    bioreactor_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """HTMX endpoint for bioreactor control panel updates."""
    bioreactor_service = BioreactorService(db)
    
    try:
        bioreactor = bioreactor_service.get_bioreactor(bioreactor_id)
        status = bioreactor_service.get_bioreactor_status(bioreactor_id)
        
        return templates.TemplateResponse("partials/bioreactor_control_panel.html", {
            "request": request,
            "bioreactor": bioreactor,
            "status": status
        })
    except Exception as e:
        return templates.TemplateResponse("partials/bioreactor_control_panel.html", {
            "request": request,
            "error": str(e)
        }) 