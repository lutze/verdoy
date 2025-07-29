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
from ...schemas.project import ProjectCreate, ProjectUpdate
from ...templates_config import templates

router = APIRouter(prefix="/app/projects", tags=["Web Projects"])

@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def list_projects_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """List projects page for web interface (HTML only)."""
    project_service = ProjectService(db)
    org_service = OrganizationService(db)
    user_organizations = org_service.get_user_organizations(current_user.id)
    
    # Get projects based on filters
    if organization_id:
        projects = project_service.get_projects_by_organization(organization_id, status)
        selected_org = org_service.get_by_id(organization_id)
    else:
        projects = []
        selected_org = None
        for org in user_organizations:
            org_projects = project_service.get_projects_by_organization(org.id, status)
            projects.extend(org_projects)
    
    # Apply search filter if provided
    if search:
        search_lower = search.lower()
        projects = [p for p in projects if 
                   search_lower in p.name.lower() or 
                   (p.description and search_lower in p.description.lower())]
    
    # Apply priority filter if provided
    if priority:
        projects = [p for p in projects if p.priority == priority]
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
            "selected_priority": priority,
            "selected_search": search,
            "stats": stats,
            "page_title": "Projects",
            "current_user": current_user
        }
    )

@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def project_create_page(
    request: Request,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    org_service = OrganizationService(db)
    organizations = org_service.get_user_organizations(current_user.id)
    return templates.TemplateResponse(
        "pages/projects/create.html",
        {
            "request": request,
            "organizations": organizations,
            "current_user": current_user,
            "page_title": "Create Project"
        }
    )

@router.get("/{project_id}", response_class=HTMLResponse, include_in_schema=False)
async def project_detail_page(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    project_service = ProjectService(db)
    project = project_service.get_by_id(project_id)
    return templates.TemplateResponse(
        "pages/projects/detail.html",
        {
            "request": request,
            "project": project,
            "current_user": current_user,
            "page_title": project.name if project else "Project Detail"
        }
    )

@router.get("/{project_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def project_edit_page(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    project_service = ProjectService(db)
    project = project_service.get_by_id(project_id)
    return templates.TemplateResponse(
        "pages/projects/edit.html",
        {
            "request": request,
            "project": project,
            "current_user": current_user,
            "page_title": f"Edit {project.name if project else 'Project'}"
        }
    )

@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
async def project_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    organization_id: UUID = Form(...),
    status: str = Form("active"),
    priority: str = Form("medium"),
    start_date: str = Form(None),
    end_date: str = Form(None),
    expected_completion: str = Form(None),
    budget: str = Form(None),
    progress_percentage: int = Form(0),
    tags: str = Form(""),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    project_service = ProjectService(db)
    org_service = OrganizationService(db)
    
    # Parse form data
    form_data = {
        "name": name,
        "description": description,
        "organization_id": organization_id,
        "status": status,
        "priority": priority,
        "budget": budget,
        "progress_percentage": progress_percentage,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else [],
        "project_metadata": {},
        "settings": {}
    }
    
    # Parse dates
    if start_date:
        form_data["start_date"] = start_date
    if end_date:
        form_data["end_date"] = end_date
    if expected_completion:
        form_data["expected_completion"] = expected_completion
    
    try:
        # Validate organization access
        user_organizations = org_service.get_user_organizations(current_user.id)
        org_ids = [str(org.id) for org in user_organizations]
        if str(organization_id) not in org_ids:
            raise HTTPException(status_code=403, detail="Access denied to organization")
        
        # Create project
        project_create_data = ProjectCreate(**form_data)
        project = project_service.create_project(project_create_data, current_user.id)
        
        return RedirectResponse(
            url=f"/app/projects/{project.id}",
            status_code=302
        )
        
    except Exception as e:
        # Get organizations for form re-render
        organizations = org_service.get_user_organizations(current_user.id)
        
        return templates.TemplateResponse(
            "pages/projects/create.html",
            {
                "request": request,
                "organizations": organizations,
                "current_user": current_user,
                "page_title": "Create Project",
                "form_data": form_data,
                "form_errors": {"general": str(e)}
            }
        )

@router.post("/{project_id}/update", response_class=HTMLResponse, include_in_schema=False)
async def project_update(
    request: Request,
    project_id: UUID,
    name: str = Form(...),
    description: str = Form(None),
    status: str = Form("active"),
    priority: str = Form("medium"),
    start_date: str = Form(None),
    end_date: str = Form(None),
    expected_completion: str = Form(None),
    budget: str = Form(None),
    progress_percentage: int = Form(0),
    tags: str = Form(""),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Update an existing project."""
    project_service = ProjectService(db)
    
    # Parse form data
    form_data = {
        "name": name,
        "description": description,
        "status": status,
        "priority": priority,
        "budget": budget,
        "progress_percentage": progress_percentage,
        "tags": [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
    }
    
    # Parse dates
    if start_date:
        form_data["start_date"] = start_date
    if end_date:
        form_data["end_date"] = end_date
    if expected_completion:
        form_data["expected_completion"] = expected_completion
    
    try:
        # Update project
        project_update_data = ProjectUpdate(**form_data)
        project = project_service.update_project(project_id, project_update_data, current_user.id)
        
        return RedirectResponse(
            url=f"/app/projects/{project.id}",
            status_code=302
        )
        
    except Exception as e:
        # Get project for form re-render
        project = project_service.get_by_id(project_id)
        
        return templates.TemplateResponse(
            "pages/projects/edit.html",
            {
                "request": request,
                "project": project,
                "current_user": current_user,
                "page_title": f"Edit {project.name if project else 'Project'}",
                "form_errors": {"general": str(e)}
            }
        )

@router.post("/{project_id}/archive", response_class=HTMLResponse, include_in_schema=False)
async def project_archive(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Archive a project."""
    project_service = ProjectService(db)
    
    try:
        project_service.archive_project(project_id)
        return RedirectResponse(
            url="/app/projects",
            status_code=302
        )
    except Exception as e:
        # Redirect back to project detail with error
        return RedirectResponse(
            url=f"/app/projects/{project_id}?error={str(e)}",
            status_code=302
        ) 