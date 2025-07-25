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
from ...models.user import User
from ...services.organization_service import OrganizationService

router = APIRouter(prefix="/api/v1/organizations", tags=["API Organizations"])

@router.get("", response_model=BaseResponse)
async def list_organizations_api(
    request: Request,
    current_user: User = Depends(get_api_user),
    db: Session = Depends(get_db)
):
    """List organizations for API clients (JSON only)."""
    org_service = OrganizationService(db)
    organizations = org_service.get_user_organizations(current_user.id)
    return BaseResponse(
        success=True,
        data={"organizations": organizations},
        message="Organizations retrieved successfully"
    )

# TODO: Add other /api/v1/organizations endpoints (POST, detail, update, delete) as needed. 