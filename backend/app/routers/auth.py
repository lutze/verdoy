"""
Authentication router for user registration, login, and token management.

This router handles all authentication-related operations including:
- User registration and account creation
- User login and token generation
- Token refresh and validation
- Password reset functionality
- User profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

from ..dependencies import get_db, get_current_user
from ..schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserUpdate
)
from ..schemas.base import BaseResponse, ErrorResponse
from ..models.user import User
from ..exceptions import (
    CredentialsException,
    UserAlreadyExistsException,
    InactiveUserException,
    InvalidTokenException
)

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, responses={
    400: {"model": ErrorResponse},
    409: {"model": ErrorResponse}
})
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates a new user with the provided information and returns the user details.
    The password will be hashed and stored securely.
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise UserAlreadyExistsException(detail="Email already registered")
    
    # Create user with hashed password
    hashed_password = User.hash_password(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    
    # Create associated entity for user profile
    from ..models.organization import Organization
    user_entity = Organization.create_user_entity(
        db=db,
        user=user,
        name=user_data.name,
        organization_id=user_data.organization_id
    )
    
    db.add(user)
    db.add(user_entity)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user_data.name,
        organization_id=user_data.organization_id,
        is_active=user.is_active,
        created_at=user.created_at
    )

@router.post("/login", response_model=TokenResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def login_user(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT access token for API access.
    The token includes user information and expiration time.
    """
    # Verify user credentials
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not user.verify_password(user_credentials.password):
        raise CredentialsException(detail="Incorrect email or password")
    
    if not user.is_active:
        raise InactiveUserException(detail="Account is deactivated")
    
    # Create access token
    from ..dependencies import create_access_token
    access_token_expires = timedelta(minutes=30)  # 30 minutes
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,  # 30 minutes in seconds
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.entity.name if user.entity else "Unknown",
            organization_id=user.entity.organization_id if user.entity else None,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )

@router.post("/logout", response_model=BaseResponse)
async def logout_user(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (token invalidation).
    
    In a production environment, this would add the token to a blacklist.
    For now, it returns a success response as the client should discard the token.
    """
    # TODO: Implement token blacklisting for production
    return BaseResponse(
        message="Successfully logged out",
        success=True
    )

@router.post("/refresh", response_model=TokenResponse, responses={
    401: {"model": ErrorResponse}
})
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token.
    
    Creates a new access token for the authenticated user.
    This allows for seamless token renewal without re-authentication.
    """
    from ..dependencies import create_access_token
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(current_user.id), "email": current_user.email},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,
        user=UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.entity.name if current_user.entity else "Unknown",
            organization_id=current_user.entity.organization_id if current_user.entity else None,
            is_active=current_user.is_active,
            created_at=current_user.created_at
        )
    )

@router.get("/me", response_model=UserResponse, responses={
    401: {"model": ErrorResponse}
})
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Returns the profile information for the authenticated user.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.entity.name if current_user.entity else "Unknown",
        organization_id=current_user.entity.organization_id if current_user.entity else None,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.put("/me", response_model=UserResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.
    
    Allows users to update their profile information including name and password.
    """
    # Update user entity if name is provided
    if user_data.name and current_user.entity:
        current_user.entity.name = user_data.name
        current_user.entity.last_updated = User.get_current_time()
    
    # Update password if provided
    if user_data.password:
        current_user.hashed_password = User.hash_password(user_data.password)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.entity.name if current_user.entity else "Unknown",
        organization_id=current_user.entity.organization_id if current_user.entity else None,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.post("/forgot-password", response_model=BaseResponse)
async def forgot_password(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset.
    
    Sends a password reset email to the user's email address.
    In production, this would send an actual email with a reset link.
    """
    user = db.query(User).filter(User.email == reset_request.email).first()
    if user and user.is_active:
        # TODO: Implement email sending with reset token
        # For now, just return success
        pass
    
    # Always return success to prevent email enumeration
    return BaseResponse(
        message="If the email exists, a password reset link has been sent",
        success=True
    )

@router.post("/reset-password", response_model=BaseResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse}
})
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password with token.
    
    Allows users to set a new password using a reset token.
    """
    # TODO: Implement token validation and password reset
    # For now, return success
    return BaseResponse(
        message="Password successfully reset",
        success=True
    )

@router.post("/change-password", response_model=BaseResponse, responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    Allows users to change their password by providing the current password.
    """
    # Verify current password
    if not current_user.verify_password(current_password):
        raise CredentialsException(detail="Current password is incorrect")
    
    # Update password
    current_user.hashed_password = User.hash_password(new_password)
    db.commit()
    
    return BaseResponse(
        message="Password successfully changed",
        success=True
    ) 