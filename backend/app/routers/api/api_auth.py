"""
API-only authentication router for /api/v1/auth endpoints.
Handles all JSON-based authentication for programmatic clients (JWT/Bearer tokens).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta, datetime

from ...dependencies import get_db, get_api_user
from ...schemas.user import UserCreate, UserLogin, UserResponse
from ...schemas.base import BaseResponse, ErrorResponse
from ...models.user import User
from ...exceptions import (
    CredentialsException,
    UserAlreadyExistsException,
    InactiveUserException,
    InvalidTokenException
)
from ...services.auth_service import AuthService
from ...utils.auth_utils import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["API Authentication"])

@router.post("/register", response_model=UserResponse, responses={
    400: {"model": ErrorResponse},
    409: {"model": ErrorResponse}
})
async def api_register_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user account (API, JSON only)."""
    try:
        body = await request.json()
        user_data = UserCreate(**body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    auth_service = AuthService(db)
    try:
        user = auth_service.register_user(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user_data.name,
            organization_id=user_data.organization_id,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            entity_id=user.entity.id if user.entity else user.id,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def api_login_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT (API, JSON only)."""
    try:
        body = await request.json()
        user_credentials = UserLogin(**body)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON data")

    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not user.check_password(user_credentials.password):
        raise CredentialsException()
    if not user.is_active:
        raise InactiveUserException(detail="Account is deactivated")

    expires_delta = timedelta(hours=1)  # Default token expiry
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=expires_delta
    )
    user.last_login = datetime.utcnow()
    db.commit()
    return BaseResponse(
        success=True,
        message="Login successful",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(expires_delta.total_seconds()),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.entity.name if user.entity else "Unknown User",
                "is_active": user.is_active
            }
        }
    )

@router.post("/logout", response_model=BaseResponse)
async def api_logout_user():
    """Logout user (API, JSON only)."""
    # For JWT, logout is typically handled client-side by deleting the token
    return BaseResponse(message="Successfully logged out", success=True)

@router.get("/profile", response_model=UserResponse)
async def api_profile(
    current_user: User = Depends(get_api_user)
):
    """Get current user profile (API, JSON only)."""
    # TODO: Implement actual user extraction from JWT
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.entity.name if current_user.entity else "Unknown User",
        organization_id=current_user.entity.organization_id if current_user.entity else None,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        entity_id=current_user.entity.id if current_user.entity else current_user.id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    ) 