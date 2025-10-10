"""
API-only organizations router for /api/v1/organizations endpoints.
Handles all JSON-based organization management for programmatic clients.
"""

from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_api_user
from ...schemas.base import BaseResponse, ErrorResponse
from ...schemas.organization import OrganizationCreate
from ...models.user import User
from ...services.organization_service_entity import OrganizationServiceEntity

router = APIRouter(prefix="/api/v1/organizations", tags=["API Organizations"])

@router.get("", response_model=BaseResponse)
async def list_organizations_api(
    request: Request,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """List organizations for API clients (JSON only)."""
    org_service = OrganizationServiceEntity(db)
    organizations = org_service.get_all_organizations()
    # Convert organizations to serializable format
    serialized_organizations = []
    for org in organizations:
        serialized_organizations.append({
            "id": str(org.id),
            "name": org.name,
            "description": org.description,
            "organization_type": org.get_property('organization_type'),
            "contact_email": org.get_property('contact_email'),
            "contact_phone": org.get_property('contact_phone'),
            "website": org.get_property('website'),
            "address": org.get_property('address'),
            "city": org.get_property('city'),
            "state": org.get_property('state'),
            "country": org.get_property('country'),
            "postal_code": org.get_property('postal_code'),
            "timezone": org.get_property('timezone', 'UTC'),
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None
        })
    
    return BaseResponse(
        success=True,
        data={"organizations": serialized_organizations},
        message="Organizations retrieved successfully"
    )

@router.post("", response_model=BaseResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse}
})
async def create_organization_api(
    request: Request,
    org_data: OrganizationCreate,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """Create a new organization for API clients (JSON only)."""
    org_service = OrganizationServiceEntity(db)
    try:
        organization = org_service.create_organization(org_data, current_user)
        return BaseResponse(
            success=True,
            data={"organization": {
                "id": str(organization.id),
                "name": organization.name,
                "description": organization.description,
                "organization_type": organization.get_property('organization_type'),
                "contact_email": organization.get_property('contact_email'),
                "contact_phone": organization.get_property('contact_phone'),
                "website": organization.get_property('website'),
                "address": organization.get_property('address'),
                "city": organization.get_property('city'),
                "state": organization.get_property('state'),
                "country": organization.get_property('country'),
                "postal_code": organization.get_property('postal_code'),
                "timezone": organization.get_property('timezone', 'UTC'),
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }},
            message="Organization created successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# TODO: Add other /api/v1/organizations endpoints (detail, update, delete) as needed. 