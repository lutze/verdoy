"""
Web-only processes router for /app/processes endpoints.
Handles all HTML-based process management for web browser clients.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from ...dependencies import get_db, get_web_user, get_optional_user
from ...models.user import User
from ...models.process import Process, ProcessInstance
from ...models.entity import Entity
from ...services.process_service import ProcessService
from ...schemas.process import ProcessCreate, ProcessUpdate, ProcessType, ProcessStatus
from ...templates_config import templates

router = APIRouter(prefix="/app/processes", tags=["Web Processes"])

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def list_processes_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    process_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_template: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """List processes page for web interface (HTML only)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        
        # Convert string status to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = ProcessStatus(status)
            except ValueError:
                pass
        
        processes_data = service.list_processes(
            current_user=current_user,
            organization_id=organization_id,
            process_type=process_type,
            status=status_enum,
            is_template=is_template,
            page=page,
            per_page=per_page,
            search=search
        )
        
        # Get organizations for filter dropdown
        organizations = []
        if current_user.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.organization_id).first()
            if org:
                organizations.append(org)
        
        return templates.TemplateResponse(
            "pages/processes/list.html",
            {
                "request": request,
                "current_user": current_user,
                "processes": processes_data.processes,
                "total": processes_data.total,
                "page": processes_data.page,
                "per_page": processes_data.per_page,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "statuses": [ps.value for ps in ProcessStatus],
                "filters": {
                    "organization_id": organization_id,
                    "process_type": process_type,
                    "status": status,
                    "is_template": is_template,
                    "search": search
                }
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Failed to load processes: {str(e)}",
                "error_code": 500
            }
        )

@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_process_form(
    request: Request,
    step: int = Query(1, ge=1, le=3),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Create process form page for web interface (HTML only)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    # Get organizations for dropdown
    organizations = []
    if current_user.organization_id:
        org = db.query(Entity).filter(Entity.id == current_user.organization_id).first()
        if org:
            organizations.append(org)
    
    return templates.TemplateResponse(
        "pages/processes/create.html",
        {
            "request": request,
            "current_user": current_user,
            "organizations": organizations,
            "process_types": [pt.value for pt in ProcessType],
            "statuses": [ps.value for ps in ProcessStatus],
            "form_data": {},
            "step": step
        }
    )

@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_process_post(
    request: Request,
    step: int = Form(...),
    name: Optional[str] = Form(None),
    version: Optional[str] = Form(None),
    process_type: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    is_template: bool = Form(False),
    parameters: Optional[list] = Form(None),
    estimated_duration: Optional[int] = Form(None),
    target_volume: Optional[float] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Handle process creation form submission."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    # Get organizations for dropdown
    organizations = []
    if current_user.organization_id:
        org = db.query(Entity).filter(Entity.id == current_user.organization_id).first()
        if org:
            organizations.append(org)
    
    # Handle multi-step form
    if step == 1:
        # Step 1: Basic Information - validate and move to step 2
        if not name or not version or not process_type or not organization_id:
            return templates.TemplateResponse(
                "pages/processes/create.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "organizations": organizations,
                    "process_types": [pt.value for pt in ProcessType],
                    "statuses": [ps.value for ps in ProcessStatus],
                    "form_data": {
                        "name": name or "",
                        "version": version or "",
                        "process_type": process_type or "",
                        "description": description or "",
                        "organization_id": organization_id or "",
                        "is_template": is_template
                    },
                    "step": 1,
                    "error_message": "Please fill in all required fields."
                }
            )
        
        # Move to step 2
        return templates.TemplateResponse(
            "pages/processes/create.html",
            {
                "request": request,
                "current_user": current_user,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "statuses": [ps.value for ps in ProcessStatus],
                "form_data": {
                    "name": name,
                    "version": version,
                    "process_type": process_type,
                    "description": description or "",
                    "organization_id": organization_id,
                    "is_template": is_template,
                    "parameters": parameters or [],
                    "estimated_duration": estimated_duration,
                    "target_volume": target_volume,
                    "notes": notes or ""
                },
                "step": 2
            }
        )
    
    elif step == 2:
        # Step 2: Process Configuration - move to step 3
        return templates.TemplateResponse(
            "pages/processes/create.html",
            {
                "request": request,
                "current_user": current_user,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "statuses": [ps.value for ps in ProcessStatus],
                "form_data": {
                    "name": name,
                    "version": version,
                    "process_type": process_type,
                    "description": description or "",
                    "organization_id": organization_id,
                    "is_template": is_template,
                    "parameters": parameters or [],
                    "estimated_duration": estimated_duration,
                    "target_volume": target_volume,
                    "notes": notes or ""
                },
                "step": 3
            }
        )
    
    elif step == 3:
        # Step 3: Create the process
        try:
            service = ProcessService(db)
            
            # Convert parameters list to dictionary format
            parameters_dict = {}
            if parameters:
                for param in parameters:
                    parameters_dict[param] = True
            
            # Create process data
            process_data = ProcessCreate(
                name=name,
                version=version,
                process_type=ProcessType(process_type),
                description=description,
                organization_id=UUID(organization_id) if organization_id else None,
                is_template=is_template,
                definition={
                    "steps": [],
                    "parameters": parameters_dict,
                    "requirements": {},
                    "outcomes": {},
                    "estimated_duration": estimated_duration,
                    "target_volume": target_volume,
                    "notes": notes
                }
            )
            
            process = service.create_process(process_data, current_user)
            
            return RedirectResponse(url=f"/app/processes/{process.id}", status_code=302)
        
        except Exception as e:
            return templates.TemplateResponse(
                "pages/processes/create.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "organizations": organizations,
                    "process_types": [pt.value for pt in ProcessType],
                    "statuses": [ps.value for ps in ProcessStatus],
                    "form_data": {
                        "name": name,
                        "version": version,
                        "process_type": process_type,
                        "description": description or "",
                        "organization_id": organization_id,
                        "is_template": is_template,
                        "parameters": parameters or [],
                        "estimated_duration": estimated_duration,
                        "target_volume": target_volume,
                        "notes": notes or ""
                    },
                    "step": 3,
                    "error_message": str(e)
                }
            )

@router.get("/{process_id}", response_class=HTMLResponse, include_in_schema=False)
async def process_detail_page(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Process detail page for web interface (HTML only)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.get_process(process_id, current_user)
        
        return templates.TemplateResponse(
            "pages/processes/detail.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Process not found: {str(e)}",
                "error_code": 404
            }
        )

@router.get("/{process_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_process_form(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Edit process form page for web interface (HTML only)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.get_process(process_id, current_user)
        
        # Get organizations for dropdown
        organizations = []
        if current_user.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.organization_id).first()
            if org:
                organizations.append(org)
        
        return templates.TemplateResponse(
            "pages/processes/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "statuses": [ps.value for ps in ProcessStatus]
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Process not found: {str(e)}",
                "error_code": 404
            }
        )

@router.post("/{process_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_process_post(
    request: Request,
    process_id: UUID,
    name: str = Form(...),
    version: str = Form(...),
    process_type: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form(...),
    is_template: bool = Form(False),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Handle process edit form submission."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        
        # Create update data
        update_data = ProcessUpdate(
            name=name,
            version=version,
            process_type=ProcessType(process_type),
            description=description,
            status=ProcessStatus(status),
            is_template=is_template
        )
        
        process = service.update_process(process_id, update_data, current_user)
        
        return RedirectResponse(url=f"/app/processes/{process.id}", status_code=302)
    
    except Exception as e:
        # Return to edit form with error
        try:
            process = service.get_process(process_id, current_user)
        except:
            process = None
        
        organizations = []
        if current_user.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.organization_id).first()
            if org:
                organizations.append(org)
        
        return templates.TemplateResponse(
            "pages/processes/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "statuses": [ps.value for ps in ProcessStatus],
                "error": str(e),
                "form_data": {
                    "name": name,
                    "version": version,
                    "process_type": process_type,
                    "description": description,
                    "status": status,
                    "is_template": is_template
                }
            }
        )

@router.post("/{process_id}/archive", response_class=HTMLResponse, include_in_schema=False)
async def archive_process_post(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Handle process archive form submission."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.archive_process(process_id, current_user)
        
        return RedirectResponse(url="/app/processes", status_code=302)
    
    except Exception as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Failed to archive process: {str(e)}",
                "error_code": 500
            }
        ) 