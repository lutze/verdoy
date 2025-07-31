"""
Process router for the LMS Core system.

This module provides API and web endpoints for process management,
including process creation, updates, execution, and monitoring.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, get_optional_user
from ..models.user import User
from ..models.entity import Entity
from ..schemas.process import (
    ProcessCreate, ProcessUpdate, ProcessResponse, ProcessListResponse,
    ProcessInstanceCreate, ProcessInstanceUpdate, ProcessInstanceResponse, ProcessInstanceListResponse,
    ProcessType, ProcessStatus, ProcessInstanceStatus, StepType
)
from ..services.process_service import ProcessService
from ..exceptions import (
    ValidationException, NotFoundException, PermissionException,
    ConflictException, BusinessLogicException
)
from ..utils.helpers import accepts_json

router = APIRouter(prefix="/api/v1/processes", tags=["processes"])


# API Endpoints (JSON responses)

@router.post("/", response_model=ProcessResponse, include_in_schema=True)
async def create_process_api(
    process_data: ProcessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new process (API endpoint)."""
    try:
        service = ProcessService(db)
        process = service.create_process(process_data, current_user)
        return ProcessResponse(**process.to_dict())
    except (ValidationException, PermissionException, ConflictException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process creation failed: {str(e)}")


@router.get("/", response_model=ProcessListResponse, include_in_schema=True)
async def list_processes_api(
    organization_id: Optional[UUID] = Query(None, description="Filter by organization"),
    process_type: Optional[str] = Query(None, description="Filter by process type"),
    status: Optional[ProcessStatus] = Query(None, description="Filter by status"),
    is_template: Optional[bool] = Query(None, description="Filter by template status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List processes with filtering and pagination (API endpoint)."""
    try:
        service = ProcessService(db)
        return service.list_processes(
            current_user=current_user,
            organization_id=organization_id,
            process_type=process_type,
            status=status,
            is_template=is_template,
            page=page,
            per_page=per_page,
            search=search
        )
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list processes: {str(e)}")


@router.get("/{process_id}", response_model=ProcessResponse, include_in_schema=True)
async def get_process_api(
    process_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a process by ID (API endpoint)."""
    try:
        service = ProcessService(db)
        process = service.get_process(process_id, current_user)
        response_data = process.to_dict()
        response_data["step_count"] = process.get_step_count()
        response_data["estimated_duration"] = process.get_estimated_duration()
        return ProcessResponse(**response_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process: {str(e)}")


@router.put("/{process_id}", response_model=ProcessResponse, include_in_schema=True)
async def update_process_api(
    process_id: UUID,
    process_data: ProcessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a process (API endpoint)."""
    try:
        service = ProcessService(db)
        process = service.update_process(process_id, process_data, current_user)
        response_data = process.to_dict()
        response_data["step_count"] = process.get_step_count()
        response_data["estimated_duration"] = process.get_estimated_duration()
        return ProcessResponse(**response_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (ValidationException, ConflictException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process update failed: {str(e)}")


@router.delete("/{process_id}", response_model=ProcessResponse, include_in_schema=True)
async def archive_process_api(
    process_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a process (API endpoint)."""
    try:
        service = ProcessService(db)
        process = service.archive_process(process_id, current_user)
        response_data = process.to_dict()
        response_data["step_count"] = process.get_step_count()
        response_data["estimated_duration"] = process.get_estimated_duration()
        return ProcessResponse(**response_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BusinessLogicException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process archive failed: {str(e)}")


# Process Instance API Endpoints

@router.post("/instances", response_model=ProcessInstanceResponse, include_in_schema=True)
async def create_process_instance_api(
    instance_data: ProcessInstanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new process instance (API endpoint)."""
    try:
        service = ProcessService(db)
        instance = service.create_process_instance(instance_data, current_user)
        response_data = instance.to_dict()
        response_data["duration"] = instance.get_duration()
        return ProcessInstanceResponse(**response_data)
    except (ValidationException, NotFoundException, PermissionException) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process instance creation failed: {str(e)}")


@router.get("/instances", response_model=ProcessInstanceListResponse, include_in_schema=True)
async def list_process_instances_api(
    process_id: Optional[UUID] = Query(None, description="Filter by process ID"),
    status: Optional[ProcessInstanceStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List process instances with filtering and pagination (API endpoint)."""
    try:
        service = ProcessService(db)
        return service.list_process_instances(
            current_user=current_user,
            process_id=process_id,
            status=status,
            page=page,
            per_page=per_page
        )
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list process instances: {str(e)}")


@router.get("/instances/{instance_id}", response_model=ProcessInstanceResponse, include_in_schema=True)
async def get_process_instance_api(
    instance_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a process instance by ID (API endpoint)."""
    try:
        service = ProcessService(db)
        instance = service.get_process_instance(instance_id, current_user)
        response_data = instance.to_dict()
        response_data["duration"] = instance.get_duration()
        return ProcessInstanceResponse(**response_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get process instance: {str(e)}")


@router.put("/instances/{instance_id}", response_model=ProcessInstanceResponse, include_in_schema=True)
async def update_process_instance_api(
    instance_id: UUID,
    instance_data: ProcessInstanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a process instance (API endpoint)."""
    try:
        service = ProcessService(db)
        instance = service.update_process_instance(instance_id, instance_data, current_user)
        response_data = instance.to_dict()
        response_data["duration"] = instance.get_duration()
        return ProcessInstanceResponse(**response_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Process instance update failed: {str(e)}")


# Web Endpoints (HTML responses)

@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def list_processes_web(
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
    """List processes page (web endpoint)."""
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
        if current_user.entity and current_user.entity.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.entity.organization_id).first()
            if org:
                organizations.append(org)
        
        return request.app.state.templates.TemplateResponse(
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
    except PermissionException as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 403
            }
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
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
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Create process form page (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    # Get organizations for dropdown
    organizations = []
    if current_user.entity and current_user.entity.organization_id:
        org = db.query(Entity).filter(Entity.id == current_user.entity.organization_id).first()
        if org:
            organizations.append(org)
    
    return request.app.state.templates.TemplateResponse(
        "pages/processes/create.html",
        {
            "request": request,
            "current_user": current_user,
            "organizations": organizations,
            "process_types": [pt.value for pt in ProcessType],
            "step_types": [st.value for st in StepType]
        }
    )


@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
async def create_process_web(
    request: Request,
    name: str = Form(...),
    version: str = Form(...),
    process_type: str = Form(...),
    description: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    is_template: bool = Form(False),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Create process (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        # Convert form data to ProcessCreate
        process_data = ProcessCreate(
            name=name,
            version=version,
            process_type=ProcessType(process_type),
            description=description,
            organization_id=UUID(organization_id) if organization_id else None,
            is_template=is_template,
            definition={
                "steps": [],
                "parameters": {},
                "estimated_duration": None,
                "requirements": {},
                "expected_outcomes": {}
            }
        )
        
        service = ProcessService(db)
        process = service.create_process(process_data, current_user)
        
        return RedirectResponse(url=f"/app/processes/{process.id}", status_code=303)
        
    except (ValidationException, PermissionException, ConflictException) as e:
        # Get organizations for form re-render
        organizations = []
        if current_user.entity and current_user.entity.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.entity.organization_id).first()
            if org:
                organizations.append(org)
        
        return request.app.state.templates.TemplateResponse(
            "pages/processes/create.html",
            {
                "request": request,
                "current_user": current_user,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "step_types": [st.value for st in StepType],
                "error_message": str(e),
                "form_data": {
                    "name": name,
                    "version": version,
                    "process_type": process_type,
                    "description": description,
                    "organization_id": organization_id,
                    "is_template": is_template
                }
            }
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Process creation failed: {str(e)}",
                "error_code": 500
            }
        )


@router.get("/{process_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_process_web(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Process detail page (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.get_process(process_id, current_user)
        
        # Get process instances
        instances_data = service.list_process_instances(
            current_user=current_user,
            process_id=process_id,
            page=1,
            per_page=5
        )
        
        return request.app.state.templates.TemplateResponse(
            "pages/processes/detail.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process,
                "instances": instances_data.instances,
                "step_count": process.get_step_count(),
                "estimated_duration": process.get_estimated_duration()
            }
        )
    except NotFoundException as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 404
            }
        )
    except PermissionException as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 403
            }
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Failed to load process: {str(e)}",
                "error_code": 500
            }
        )


@router.get("/{process_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_process_form(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Edit process form page (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.get_process(process_id, current_user)
        
        # Get organizations for dropdown
        organizations = []
        if current_user.entity and current_user.entity.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.entity.organization_id).first()
            if org:
                organizations.append(org)
        
        return request.app.state.templates.TemplateResponse(
            "pages/processes/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "step_types": [st.value for st in StepType]
            }
        )
    except NotFoundException as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 404
            }
        )
    except PermissionException as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 403
            }
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Failed to load process: {str(e)}",
                "error_code": 500
            }
        )


@router.post("/{process_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_process_web(
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
    """Edit process (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        # Convert form data to ProcessUpdate
        process_data = ProcessUpdate(
            name=name,
            version=version,
            process_type=ProcessType(process_type),
            description=description,
            status=ProcessStatus(status),
            is_template=is_template
        )
        
        service = ProcessService(db)
        process = service.update_process(process_id, process_data, current_user)
        
        return RedirectResponse(url=f"/app/processes/{process.id}", status_code=303)
        
    except (ValidationException, PermissionException, ConflictException) as e:
        # Get process for form re-render
        try:
            service = ProcessService(db)
            process = service.get_process(process_id, current_user)
        except:
            process = None
        
        # Get organizations for form re-render
        organizations = []
        if current_user.entity and current_user.entity.organization_id:
            org = db.query(Entity).filter(Entity.id == current_user.entity.organization_id).first()
            if org:
                organizations.append(org)
        
        return request.app.state.templates.TemplateResponse(
            "pages/processes/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "process": process,
                "organizations": organizations,
                "process_types": [pt.value for pt in ProcessType],
                "step_types": [st.value for st in StepType],
                "error_message": str(e),
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
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Process update failed: {str(e)}",
                "error_code": 500
            }
        )


@router.post("/{process_id}/archive", response_class=HTMLResponse, include_in_schema=False)
async def archive_process_web(
    request: Request,
    process_id: UUID,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Archive process (web endpoint)."""
    if not current_user:
        return RedirectResponse(url="/app/login", status_code=303)
    
    try:
        service = ProcessService(db)
        process = service.archive_process(process_id, current_user)
        
        return RedirectResponse(url="/app/processes", status_code=303)
        
    except (NotFoundException, PermissionException, BusinessLogicException) as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": str(e),
                "error_code": 400
            }
        )
    except Exception as e:
        return request.app.state.templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "current_user": current_user,
                "error_message": f"Process archive failed: {str(e)}",
                "error_code": 500
            }
        ) 