"""
Projects router for laboratory project management.

This router handles:
- Project CRUD operations for both web and API clients
- Project status and progress management  
- Project statistics and reporting
- Organization-project relationships
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import date

from ..dependencies import get_db, get_current_user
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..services.project_service import ProjectService
from ..services.organization_service import OrganizationService
from ..schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStatistics
from ..templates_config import templates

router = APIRouter(tags=["Projects"])

def accepts_json(request: Request) -> bool:
    """Check if client accepts JSON responses."""
    accept_header = request.headers.get("accept", "")
    return (
        "application/json" in accept_header or
        "application/ld+json" in accept_header or
        request.url.path.startswith("/api/")
    )

# ============================================================================
# HTML PAGES (GET ROUTES)
# ============================================================================

@router.get("/app/projects", response_class=HTMLResponse, include_in_schema=False)
async def list_projects_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List projects page for web interface."""
    if accepts_json(request):
        return await list_projects_api(request, organization_id, status, current_user, db)
    
    try:
        project_service = ProjectService(db)
        org_service = OrganizationService(db)
        
        # Get user's organizations for filter dropdown
        user_organizations = org_service.get_user_organizations(current_user.id)
        
        # Get projects based on filters
        if organization_id:
            projects = project_service.get_projects_by_organization(organization_id, status)
            selected_org = org_service.get_by_id(organization_id)
        else:
            # Get projects from all user's organizations
            projects = []
            selected_org = None
            for org in user_organizations:
                org_projects = project_service.get_projects_by_organization(org.id, status)
                projects.extend(org_projects)
        
        # Get project statistics
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
    except Exception as e:
        # Handle error gracefully
        return templates.TemplateResponse(
            "pages/projects/list.html",
            {
                "request": request,
                "user": current_user,
                "projects": [],
                "organizations": [],
                "error": str(e),
                "page_title": "Projects"
            }
        )

@router.get("/app/projects/create", response_class=HTMLResponse, include_in_schema=False)
async def create_project_page(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create project page for web interface."""
    try:
        org_service = OrganizationService(db)
        organizations = org_service.get_user_organizations(current_user.id)
        
        return templates.TemplateResponse(
            "pages/projects/create.html",
            {
                "request": request,
                "user": current_user,
                "organizations": organizations,
                "selected_organization_id": organization_id,
                "page_title": "Create Project"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to load create project page")

@router.post("/app/projects/create", response_class=HTMLResponse, include_in_schema=False)
async def create_project_page_submit(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    organization_id: UUID = Form(...),
    status: str = Form("active"),
    priority: str = Form("medium"),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    expected_completion: Optional[str] = Form(None),
    budget: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create project form submission for web interface."""
    try:
        # Parse form data
        start_date_parsed = date.fromisoformat(start_date) if start_date else None
        end_date_parsed = date.fromisoformat(end_date) if end_date else None
        expected_completion_parsed = date.fromisoformat(expected_completion) if expected_completion else None
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Create project data
        project_data = ProjectCreate(
            name=name,
            description=description,
            organization_id=organization_id,
            status=status,
            priority=priority,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            expected_completion=expected_completion_parsed,
            budget=budget,
            tags=tags_list,
            project_lead_id=current_user.id  # Set current user as project lead
        )
        
        # Create project
        project_service = ProjectService(db)
        project = project_service.create_project(project_data, current_user.id)
        
        # Redirect to project detail page
        return RedirectResponse(
            url=f"/app/projects/{project.id}",
            status_code=303
        )
        
    except Exception as e:
        # Return form with error
        org_service = OrganizationService(db)
        organizations = org_service.get_user_organizations(current_user.id)
        
        return templates.TemplateResponse(
            "pages/projects/create.html",
            {
                "request": request,
                "user": current_user,
                "organizations": organizations,
                "page_title": "Create Project",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "description": description,
                    "organization_id": str(organization_id),
                    "status": status,
                    "priority": priority,
                    "start_date": start_date,
                    "end_date": end_date,
                    "expected_completion": expected_completion,
                    "budget": budget,
                    "tags": tags
                }
            }
        )

@router.get("/app/projects/{project_id}", response_class=HTMLResponse, include_in_schema=False)
async def get_project_page(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Project detail page for web interface."""
    if accepts_json(request):
        return await get_project_api(request, project_id, current_user, db)
    
    try:
        project_service = ProjectService(db)
        project = project_service.get_by_id_or_raise(project_id)
        
        # Get organization info
        org_service = OrganizationService(db)
        organization = org_service.get_by_id_or_raise(project.organization_id)
        
        return templates.TemplateResponse(
            "pages/projects/detail.html",
            {
                "request": request,
                "user": current_user,
                "project": project,
                "organization": organization,
                "page_title": f"Project: {project.name}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Project not found")

@router.get("/app/projects/{project_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_project_page(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit project page for web interface."""
    try:
        project_service = ProjectService(db)
        project = project_service.get_by_id_or_raise(project_id)
        
        org_service = OrganizationService(db)
        organizations = org_service.get_user_organizations(current_user.id)
        
        return templates.TemplateResponse(
            "pages/projects/edit.html",
            {
                "request": request,
                "user": current_user,
                "project": project,
                "organizations": organizations,
                "page_title": f"Edit Project: {project.name}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail="Project not found")

@router.post("/app/projects/{project_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit_project_page_submit(
    request: Request,
    project_id: UUID,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form("active"),
    priority: str = Form("medium"),
    start_date: Optional[str] = Form(None),
    end_date: Optional[str] = Form(None),
    expected_completion: Optional[str] = Form(None),
    budget: Optional[str] = Form(None),
    progress_percentage: int = Form(0),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit project form submission for web interface."""
    try:
        # Parse form data
        start_date_parsed = date.fromisoformat(start_date) if start_date else None
        end_date_parsed = date.fromisoformat(end_date) if end_date else None
        expected_completion_parsed = date.fromisoformat(expected_completion) if expected_completion else None
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Create project update data
        project_data = ProjectUpdate(
            name=name,
            description=description,
            status=status,
            priority=priority,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            expected_completion=expected_completion_parsed,
            budget=budget,
            progress_percentage=progress_percentage,
            tags=tags_list
        )
        
        # Update project
        project_service = ProjectService(db)
        project = project_service.update(project_id, project_data)
        
        # Redirect to project detail page
        return RedirectResponse(
            url=f"/app/projects/{project.id}",
            status_code=303
        )
        
    except Exception as e:
        # Return form with error
        project_service = ProjectService(db)
        project = project_service.get_by_id_or_raise(project_id)
        
        org_service = OrganizationService(db)
        organizations = org_service.get_user_organizations(current_user.id)
        
        return templates.TemplateResponse(
            "pages/projects/edit.html",
            {
                "request": request,
                "user": current_user,
                "project": project,
                "organizations": organizations,
                "page_title": f"Edit Project: {project.name}",
                "error": str(e),
                "form_data": {
                    "name": name,
                    "description": description,
                    "status": status,
                    "priority": priority,
                    "start_date": start_date,
                    "end_date": end_date,
                    "expected_completion": expected_completion,
                    "budget": budget,
                    "progress_percentage": progress_percentage,
                    "tags": tags
                }
            }
        )

# ============================================================================
# JSON API ROUTES  
# ============================================================================

@router.get("/api/v1/projects", response_model=BaseResponse)
async def list_projects_api(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List projects for API clients."""
    project_service = ProjectService(db)
    
    if organization_id:
        projects = project_service.get_projects_by_organization(organization_id, status)
    else:
        # Get projects from all user's organizations
        org_service = OrganizationService(db)
        user_organizations = org_service.get_user_organizations(current_user.id)
        projects = []
        for org in user_organizations:
            org_projects = project_service.get_projects_by_organization(org.id, status)
            projects.extend(org_projects)
    
    return BaseResponse(
        success=True,
        data={"projects": projects},
        message="Projects retrieved successfully"
    )

@router.post("/api/v1/projects", response_model=BaseResponse)
async def create_project_api(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create project for API clients."""
    project_service = ProjectService(db)
    project = project_service.create_project(project_data, current_user.id)
    
    return BaseResponse(
        success=True,
        data={"project": project},
        message="Project created successfully"
    )

@router.get("/api/v1/projects/{project_id}", response_model=BaseResponse)
async def get_project_api(
    request: Request,
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details for API clients."""
    project_service = ProjectService(db)
    project = project_service.get_by_id_or_raise(project_id)
    
    return BaseResponse(
        success=True,
        data={"project": project},
        message="Project retrieved successfully"
    )

@router.put("/api/v1/projects/{project_id}", response_model=BaseResponse)
async def update_project_api(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project for API clients."""
    project_service = ProjectService(db)
    project = project_service.update(project_id, project_data)
    
    return BaseResponse(
        success=True,
        data={"project": project},
        message="Project updated successfully"
    )

@router.delete("/api/v1/projects/{project_id}", response_model=BaseResponse)
async def delete_project_api(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive project for API clients."""
    project_service = ProjectService(db)
    project_service.archive_project(project_id)
    
    return BaseResponse(
        success=True,
        data={"project_id": str(project_id)},
        message="Project archived successfully"
    ) 