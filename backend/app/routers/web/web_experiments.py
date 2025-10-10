"""
Web experiment routes for the VerdoyLab API.

This module provides HTML endpoints for experiment management
in the web interface, including list, create, edit, and detail views.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ...dependencies import get_db, get_current_user, get_optional_user
from ...services.experiment_service_entity import ExperimentServiceEntity
from ...services.project_service import ProjectService
from ...services.process_service_entity import ProcessServiceEntity
from ...services.bioreactor_service import BioreactorService
from ...services.organization_service_entity import OrganizationServiceEntity
from ...schemas.experiment import (
    ExperimentCreate, ExperimentUpdate, ExperimentFilterRequest,
    ExperimentControlRequest, ExperimentStatsResponse
)
from ...models.user import User
from ...templates_config import get_templates

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/app/experiments", tags=["experiments"])


def get_user_organization_id(db: Session, user: User) -> Optional[UUID]:
    """Get the user's primary organization ID."""
    org_service = OrganizationServiceEntity(db)
    user_organizations = org_service.get_user_organizations(user.id)
    if user_organizations:
        return user_organizations[0].id
    return None


@router.get("", response_class=HTMLResponse, include_in_schema=False)
async def experiment_list_page(
    request: Request,
    status: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    process_id: Optional[str] = Query(None),
    bioreactor_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Experiment list page."""
    try:
        templates = get_templates()
        
        if not current_user:
            return RedirectResponse(url="/app/login", status_code=302)
        
        # Get user's organizations
        org_service = OrganizationServiceEntity(db)
        user_organizations = org_service.get_user_organizations(current_user.id)
        if not user_organizations:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "No organization access",
                    "current_user": current_user
                }
            )
        # Use the first organization for now (could be enhanced to support multiple orgs)
        organization_id = user_organizations[0].id
        
        # Build filters
        filters = ExperimentFilterRequest(
            status=status,
            project_id=UUID(project_id) if project_id else None,
            process_id=UUID(process_id) if process_id else None,
            bioreactor_id=UUID(bioreactor_id) if bioreactor_id else None,
            search=search,
            page=page,
            page_size=page_size
        )
        
        # Get experiments
        experiment_service = ExperimentServiceEntity(db)
        experiments, total_count = experiment_service.get_user_accessible_experiments(
            current_user.id, filters
        )
        
        # Get related data for display
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        # Get projects, processes, and bioreactors for filters
        projects = project_service.get_projects_by_organization(organization_id)
        processes = process_service.get_processes_by_organization(organization_id)
        bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size
        
        return templates.TemplateResponse(
            "pages/experiments/list.html",
            {
                "request": request,
                "current_user": current_user,
                "experiments": experiments,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "filters": filters,
                "projects": projects,
                "processes": processes,
                "bioreactors": bioreactors,
                "status_options": ["draft", "active", "paused", "completed", "failed", "archived"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading experiment list page: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to load experiments",
                "current_user": current_user
            }
        )


@router.get("/create", response_class=HTMLResponse, include_in_schema=False)
async def experiment_create_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Experiment create page."""
    try:
        templates = get_templates()
        
        if not current_user:
            return RedirectResponse(url="/app/login", status_code=302)
        
        # Get user's organizations
        org_service = OrganizationServiceEntity(db)
        user_organizations = org_service.get_user_organizations(current_user.id)
        if not user_organizations:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "No organization access",
                    "current_user": current_user
                }
            )
        # Use the first organization for now (could be enhanced to support multiple orgs)
        organization_id = user_organizations[0].id
        
        # Get available projects, processes, and bioreactors
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        projects = project_service.get_projects_by_organization(organization_id)
        processes = process_service.get_processes_by_organization(organization_id)
        bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
        
        # Filter available bioreactors (not running experiments)
        available_bioreactors = [b for b in bioreactors if not b.is_running_experiment()]
        
        return templates.TemplateResponse(
            "pages/experiments/create.html",
            {
                "request": request,
                "current_user": current_user,
                "projects": projects,
                "processes": processes,
                "bioreactors": available_bioreactors,
                "form_data": {},
                "errors": {}
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading experiment create page: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to load create page",
                "current_user": current_user
            }
        )


@router.post("/create", response_class=HTMLResponse, include_in_schema=False)
async def experiment_create_post(
    request: Request,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    project_id: str = Form(...),
    process_id: str = Form(...),
    bioreactor_id: str = Form(...),
    total_trials: int = Form(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create experiment POST handler."""
    try:
        templates = get_templates()
        
        # Get user's organizations
        org_service = OrganizationServiceEntity(db)
        user_organizations = org_service.get_user_organizations(current_user.id)
        if not user_organizations:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "No organization access",
                    "current_user": current_user
                }
            )
        # Use the first organization for now (could be enhanced to support multiple orgs)
        organization_id = user_organizations[0].id
        
        # Prepare form data
        form_data = {
            "name": name,
            "description": description,
            "project_id": project_id,
            "process_id": process_id,
            "bioreactor_id": bioreactor_id,
            "total_trials": total_trials
        }
        
        # Validate required fields
        errors = {}
        if not name.strip():
            errors["name"] = "Experiment name is required"
        
        if not project_id:
            errors["project_id"] = "Project is required"
        
        if not process_id:
            errors["process_id"] = "Process is required"
        
        if not bioreactor_id:
            errors["bioreactor_id"] = "Bioreactor is required"
        
        if total_trials < 1:
            errors["total_trials"] = "Total trials must be at least 1"
        
        if errors:
            # Get available data for form re-population
            project_service = ProjectService(db)
            process_service = ProcessServiceEntity(db)
            bioreactor_service = BioreactorService(db)
            
            projects = project_service.get_projects_by_organization(organization_id)
            processes = process_service.get_processes_by_organization(organization_id)
            bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
            available_bioreactors = [b for b in bioreactors if not b.is_running_experiment()]
            
            return templates.TemplateResponse(
                "pages/experiments/create.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "projects": projects,
                    "processes": processes,
                    "bioreactors": available_bioreactors,
                    "form_data": form_data,
                    "errors": errors
                }
            )
        
        # Create experiment
        experiment_service = ExperimentServiceEntity(db)
        experiment_data = ExperimentCreate(
            name=name.strip(),
            description=description.strip() if description else None,
            project_id=UUID(project_id),
            process_id=UUID(process_id),
            bioreactor_id=UUID(bioreactor_id),
            total_trials=total_trials,
            parameters={},  # Will be configured in next step
            metadata={}     # Will be configured in next step
        )
        
        experiment = experiment_service.create_experiment(experiment_data, current_user)
        
        # Redirect to experiment detail page
        return RedirectResponse(
            url=f"/app/experiments/{experiment.id}",
            status_code=302
        )
        
    except HTTPException as e:
        # Get available data for form re-population
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        projects = project_service.get_projects_by_organization(organization_id)
        processes = process_service.get_processes_by_organization(organization_id)
        bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
        available_bioreactors = [b for b in bioreactors if not b.is_running_experiment()]
        
        return templates.TemplateResponse(
            "pages/experiments/create.html",
            {
                "request": request,
                "current_user": current_user,
                "projects": projects,
                "processes": processes,
                "bioreactors": available_bioreactors,
                "form_data": form_data,
                "errors": {"general": e.detail}
            }
        )
    except Exception as e:
        logger.error(f"Error creating experiment: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to create experiment",
                "current_user": current_user
            }
        )


@router.get("/{experiment_id}", response_class=HTMLResponse, include_in_schema=False)
async def experiment_detail_page(
    request: Request,
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Experiment detail page."""
    try:
        templates = get_templates()
        
        if not current_user:
            return RedirectResponse(url="/app/login", status_code=302)
        
        # Get experiment
        experiment_service = ExperimentServiceEntity(db)
        experiment = experiment_service.get_experiment_by_id(experiment_id)
        
        if not experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Check access (user must be in same organization)
        user_org_id = get_user_organization_id(db, current_user)
        if experiment.organization_id != user_org_id:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "Access denied",
                    "current_user": current_user
                }
            )
        
        # Get related data
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        project = project_service.get_by_id(experiment.project_id) if experiment.project_id else None
        process = process_service.get_process(experiment.process_id, current_user) if experiment.process_id else None
        bioreactor = bioreactor_service.get_bioreactor(experiment.bioreactor_id) if experiment.bioreactor_id else None
        
        # Get trials
        trials = experiment_service.get_trials_by_experiment(experiment_id)
        
        return templates.TemplateResponse(
            "pages/experiments/detail.html",
            {
                "request": request,
                "current_user": current_user,
                "experiment": experiment,
                "project": project,
                "process": process,
                "bioreactor": bioreactor,
                "trials": trials
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading experiment detail page: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to load experiment",
                "current_user": current_user
            }
        )


@router.get("/{experiment_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def experiment_edit_page(
    request: Request,
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Experiment edit page."""
    try:
        templates = get_templates()
        
        if not current_user:
            return RedirectResponse(url="/app/login", status_code=302)
        
        # Get experiment
        experiment_service = ExperimentServiceEntity(db)
        experiment = experiment_service.get_experiment_by_id(experiment_id)
        
        if not experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Check access
        user_org_id = get_user_organization_id(db, current_user)
        if experiment.organization_id != user_org_id:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "Access denied",
                    "current_user": current_user
                }
            )
        
        # Prevent editing running experiments
        if experiment.is_running:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 409,
                    "error_message": "Cannot edit experiment while it is running",
                    "current_user": current_user
                }
            )
        
        # Get available projects, processes, and bioreactors
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        organization_id = get_user_organization_id(db, current_user)
        projects = project_service.get_projects_by_organization(organization_id)
        processes = process_service.get_processes_by_organization(organization_id)
        bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
        
        return templates.TemplateResponse(
            "pages/experiments/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "experiment": experiment,
                "projects": projects,
                "processes": processes,
                "bioreactors": bioreactors,
                "form_data": {
                    "name": experiment.name,
                    "description": experiment.description,
                    "project_id": str(experiment.project_id) if experiment.project_id else "",
                    "process_id": str(experiment.process_id) if experiment.process_id else "",
                    "bioreactor_id": str(experiment.bioreactor_id) if experiment.bioreactor_id else "",
                    "total_trials": experiment.total_trials
                },
                "errors": {}
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading experiment edit page: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to load edit page",
                "current_user": current_user
            }
        )


@router.post("/{experiment_id}/edit", response_class=HTMLResponse, include_in_schema=False)
async def experiment_edit_post(
    request: Request,
    experiment_id: UUID,
    name: str = Form(...),
    description: Optional[str] = Form(None),
    project_id: str = Form(...),
    process_id: str = Form(...),
    bioreactor_id: str = Form(...),
    total_trials: int = Form(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update experiment POST handler."""
    try:
        templates = get_templates()
        
        # Get experiment
        experiment_service = ExperimentServiceEntity(db)
        experiment = experiment_service.get_experiment_by_id(experiment_id)
        
        if not experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Check access
        if experiment.organization_id != current_user.get_primary_organization_id():
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "Access denied",
                    "current_user": current_user
                }
            )
        
        # Prepare form data
        form_data = {
            "name": name,
            "description": description,
            "project_id": project_id,
            "process_id": process_id,
            "bioreactor_id": bioreactor_id,
            "total_trials": total_trials
        }
        
        # Validate required fields
        errors = {}
        if not name.strip():
            errors["name"] = "Experiment name is required"
        
        if not project_id:
            errors["project_id"] = "Project is required"
        
        if not process_id:
            errors["process_id"] = "Process is required"
        
        if not bioreactor_id:
            errors["bioreactor_id"] = "Bioreactor is required"
        
        if total_trials < 1:
            errors["total_trials"] = "Total trials must be at least 1"
        
        if errors:
            # Get available data for form re-population
            project_service = ProjectService(db)
            process_service = ProcessServiceEntity(db)
            bioreactor_service = BioreactorService(db)
            
            organization_id = get_user_organization_id(db, current_user)
            projects = project_service.get_projects_by_organization(organization_id)
            processes = process_service.get_processes_by_organization(organization_id)
            bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
            
            return templates.TemplateResponse(
                "pages/experiments/edit.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "experiment": experiment,
                    "projects": projects,
                    "processes": processes,
                    "bioreactors": bioreactors,
                    "form_data": form_data,
                    "errors": errors
                }
            )
        
        # Update experiment
        experiment_data = ExperimentUpdate(
            name=name.strip(),
            description=description.strip() if description else None,
            total_trials=total_trials
        )
        
        updated_experiment = experiment_service.update_experiment(
            experiment_id, experiment_data, current_user
        )
        
        if not updated_experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Redirect to experiment detail page
        return RedirectResponse(
            url=f"/app/experiments/{experiment_id}",
            status_code=302
        )
        
    except HTTPException as e:
        # Get available data for form re-population
        project_service = ProjectService(db)
        process_service = ProcessServiceEntity(db)
        bioreactor_service = BioreactorService(db)
        
        organization_id = get_user_organization_id(db, current_user)
        projects = project_service.get_projects_by_organization(organization_id)
        processes = process_service.get_processes_by_organization(organization_id)
        bioreactors = bioreactor_service.get_bioreactors_by_organization(organization_id)
        
        return templates.TemplateResponse(
            "pages/experiments/edit.html",
            {
                "request": request,
                "current_user": current_user,
                "experiment": experiment,
                "projects": projects,
                "processes": processes,
                "bioreactors": bioreactors,
                "form_data": form_data,
                "errors": {"general": e.detail}
            }
        )
    except Exception as e:
        logger.error(f"Error updating experiment: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to update experiment",
                "current_user": current_user
            }
        )


@router.post("/{experiment_id}/archive", response_class=HTMLResponse, include_in_schema=False)
async def experiment_archive_post(
    request: Request,
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Archive experiment POST handler."""
    try:
        templates = get_templates()
        
        # Archive experiment
        experiment_service = ExperimentServiceEntity(db)
        archived_experiment = experiment_service.archive_experiment(experiment_id, current_user.id)
        
        if not archived_experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Redirect to experiment list
        return RedirectResponse(
            url="/app/experiments",
            status_code=302
        )
        
    except HTTPException as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": e.status_code,
                "error_message": e.detail,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error archiving experiment: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to archive experiment",
                "current_user": current_user
            }
        )


@router.get("/{experiment_id}/monitor", response_class=HTMLResponse, include_in_schema=False)
async def experiment_monitor_page(
    request: Request,
    experiment_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Experiment monitor page."""
    try:
        templates = get_templates()
        
        if not current_user:
            return RedirectResponse(url="/app/login", status_code=302)
        
        # Get experiment
        experiment_service = ExperimentServiceEntity(db)
        experiment = experiment_service.get_experiment_by_id(experiment_id)
        
        if not experiment:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 404,
                    "error_message": "Experiment not found",
                    "current_user": current_user
                }
            )
        
        # Check access
        user_org_id = get_user_organization_id(db, current_user)
        if experiment.organization_id != user_org_id:
            return templates.TemplateResponse(
                "pages/error.html",
                {
                    "request": request,
                    "error_code": 403,
                    "error_message": "Access denied",
                    "current_user": current_user
                }
            )
        
        # Get bioreactor for real-time data
        bioreactor = None
        if experiment.bioreactor_id:
            bioreactor_service = BioreactorService(db)
            bioreactor = bioreactor_service.get_bioreactor_by_id(experiment.bioreactor_id)
        
        return templates.TemplateResponse(
            "pages/experiments/monitor.html",
            {
                "request": request,
                "current_user": current_user,
                "experiment": experiment,
                "bioreactor": bioreactor
            }
        )
        
    except Exception as e:
        logger.error(f"Error loading experiment monitor page: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to load monitor page",
                "current_user": current_user
            }
        )


@router.post("/{experiment_id}/control", response_class=HTMLResponse, include_in_schema=False)
async def experiment_control_post(
    request: Request,
    experiment_id: UUID,
    action: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Control experiment POST handler."""
    try:
        templates = get_templates()
        
        # Control experiment
        experiment_service = ExperimentServiceEntity(db)
        control_data = ExperimentControlRequest(action=action)
        
        response = experiment_service.control_experiment(
            experiment_id, control_data, current_user
        )
        
        # Redirect back to experiment detail page
        return RedirectResponse(
            url=f"/app/experiments/{experiment_id}",
            status_code=302
        )
        
    except HTTPException as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": e.status_code,
                "error_message": e.detail,
                "current_user": current_user
            }
        )
    except Exception as e:
        logger.error(f"Error controlling experiment: {e}")
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error_code": 500,
                "error_message": "Failed to control experiment",
                "current_user": current_user
            }
        ) 