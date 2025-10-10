"""
API-only projects router for /api/v1/projects endpoints.
Handles all JSON-based project management for programmatic clients.
"""

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_api_user
from ...schemas.base import BaseResponse, ErrorResponse
from ...models.user import User
from ...services.project_service import ProjectService
from ...services.organization_service_entity import OrganizationServiceEntity

router = APIRouter(prefix="/api/v1/projects", tags=["API Projects"])

@router.get("", response_model=BaseResponse)
async def list_projects_api(
    request: Request,
    organization_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """List projects for API clients (JSON only)."""
    project_service = ProjectService(db)
    if organization_id:
        projects = project_service.get_projects_by_organization(organization_id, status)
    else:
        org_service = OrganizationServiceEntity(db)
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

# TODO: Add other /api/v1/projects endpoints (POST, detail, update, delete) as needed. 