"""
Authentication router for user registration, login, and token management.

This router handles all authentication-related operations including:
- User registration and account creation
- User login and token generation
- Token refresh and validation
- Password reset functionality
- User profile management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBearer
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional

logger = logging.getLogger(__name__)

from ..dependencies import get_db
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
from ..templates_config import templates

router = APIRouter(tags=["Authentication"])

def accepts_json(request: Request) -> bool:
    """Check if client prefers JSON responses"""
    accept_header = request.headers.get("accept", "")
    return (
        "application/json" in accept_header or
        "application/ld+json" in accept_header or
        request.url.path.startswith("/api/")
    )

# ============================================================================
# DUAL-PURPOSE ROUTES (HTML + JSON)
# ============================================================================

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Display login page for web browsers or return login info for API clients."""
    if accepts_json(request):
        return {"login_url": "/api/v1/auth/login", "method": "POST"}
    else:
        return templates.TemplateResponse("pages/auth/login.html", {
            "request": request,
            "error": error,
            "message": message
        })

@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Display registration page for web browsers or return registration info for API clients."""
    if accepts_json(request):
        return {"register_url": "/api/v1/auth/register", "method": "POST"}
    else:
        organizations = []  # TODO: Implement organization loading
        return templates.TemplateResponse("pages/auth/register.html", {
            "request": request,
            "organizations": organizations
        })

# Remove the old /profile route and replace it with the new /app/admin/profile route
@router.get("/admin/profile", response_class=HTMLResponse, include_in_schema=False)
async def profile_page(request: Request):
    if accepts_json(request):
        return {"user": {"name": "Test User", "email": "test@example.com"}, "organization": None, "api_keys": []}
    else:
        return templates.TemplateResponse("pages/auth/profile.html", {
            "request": request,
            "user": {"name": "Test User", "email": "test@example.com"},
            "organization": None,
            "api_keys": []
        })

# ============================================================================
# AUTHENTICATION ENDPOINTS (POST ROUTES)
# ============================================================================

@router.post("/register", responses={
    400: {"model": ErrorResponse},
    409: {"model": ErrorResponse}
})
async def register_user(
    request: Request,
    db: Session = Depends(get_db),
    # Form data for HTML forms
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    new_organization_name: Optional[str] = Form(None),
    accept_terms: Optional[str] = Form(None)
):
    """Register a new user account with both HTML and JSON support."""
    from ..services.auth_service import AuthService
    
    # Check if this is a JSON request
    if accepts_json(request):
        # Parse JSON body manually for API calls
        try:
            body = await request.json()
            user_data = UserCreate(**body)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
    else:
        # Handle form data
        if not all([name, email, password]):
            return templates.TemplateResponse("pages/auth/register.html", {
                "request": request,
                "error": "All fields are required",
                "name": name,
                "email": email,
                "organizations": []
            })
        
        # Handle "create_new" organization case
        if organization_id == "create_new":
            user_data = UserCreate(
                name=name,
                email=email,
                password=password,
                organization_id=None
            )
        else:
            # Convert string to UUID if provided
            org_id = None
            if organization_id and organization_id != "create_new":
                try:
                    import uuid
                    org_id = uuid.UUID(organization_id)
                except ValueError:
                    return templates.TemplateResponse("pages/auth/register.html", {
                        "request": request,
                        "error": "Invalid organization ID",
                        "name": name,
                        "email": email,
                        "organizations": []
                    })
            
            user_data = UserCreate(
                name=name,
                email=email,
                password=password,
                organization_id=org_id
            )
    
    # Use AuthService for proper user registration
    auth_service = AuthService(db)
    
    try:
        # Always create user without organization first for a more robust flow
        user_creation_data = UserCreate(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            organization_id=None  # Create user without organization initially
        )
        
        # Register user through service layer
        user = auth_service.register_user(user_creation_data)
        logger.info(f"User created successfully: {user.email}")
        
        # Handle organization creation/assignment AFTER user creation
        final_organization_id = None
        
        if organization_id == "create_new" and new_organization_name:
            # Create new organization and assign user to it
            from ..services.organization_service import OrganizationService
            from ..schemas.organization import OrganizationCreate
            
            org_service = OrganizationService(db)
            org_data = OrganizationCreate(
                name=new_organization_name,
                description=f"Organization created by {user_data.name}",
                organization_type="small_business"
            )
            
            try:
                organization = org_service.create_organization(org_data, user.id)
                
                # Update user's entity with the new organization
                if user.entity:
                    user.entity.organization_id = organization.id
                    db.commit()
                    final_organization_id = organization.id
                    
                logger.info(f"Created organization '{organization.name}' and assigned user {user.email}")
                
            except Exception as e:
                # If organization creation fails, log error but don't fail user creation
                logger.error(f"Failed to create organization for user {user.email}: {e}")
                # User creation still succeeded, just without the custom organization
                
        elif user_data.organization_id:
            # Assign user to existing organization
            if user.entity:
                user.entity.organization_id = user_data.organization_id
                db.commit()
                final_organization_id = user_data.organization_id
                logger.info(f"Assigned user {user.email} to existing organization {user_data.organization_id}")
        
        # Return response based on content type
        if accepts_json(request):
            return UserResponse(
                id=user.id,
                email=user.email,
                name=user_data.name,
                organization_id=final_organization_id,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                entity_id=user.entity.id if user.entity else user.id,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        else:
            # Redirect to login with success message
            return RedirectResponse(
                url="/app/login?message=Account created successfully! Please sign in.",
                status_code=303
            )
            
    except UserAlreadyExistsException as e:
        if accepts_json(request):
            raise HTTPException(status_code=409, detail=str(e))
        else:
            return templates.TemplateResponse("pages/auth/register.html", {
                "request": request,
                "error": "Email already registered",
                "name": user_data.name,
                "email": user_data.email,
                "organizations": []
            })
    except Exception as e:
        logger.error(f"Error during user registration: {e}")
        if accepts_json(request):
            raise HTTPException(status_code=500, detail="Registration failed")
        else:
            return templates.TemplateResponse("pages/auth/register.html", {
                "request": request,
                "error": "Registration failed. Please try again.",
                "name": user_data.name,
                "email": user_data.email,
                "organizations": []
            })

@router.post("/login", responses={
    401: {"model": ErrorResponse},
    400: {"model": ErrorResponse}
})
async def login_user(
    request: Request,
    db: Session = Depends(get_db),
    # Form data for HTML forms
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    remember_me: Optional[str] = Form(None)
):
    """Authenticate user with both HTML and JSON support."""
    
    # Check if this is a JSON request
    if accepts_json(request):
        # Parse JSON body manually for API calls
        try:
            body = await request.json()
            user_credentials = UserLogin(**body)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON data")
    else:
        # Handle form data
        if not email or not password:
            return templates.TemplateResponse("pages/auth/login.html", {
                "request": request,
                "error": "Email and password are required",
                "email": email
            })
        
        user_credentials = UserLogin(email=email, password=password)
    
    # Verify user credentials
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not user.check_password(user_credentials.password):
        if accepts_json(request):
            raise CredentialsException(detail="Incorrect email or password")
        else:
            return templates.TemplateResponse("pages/auth/login.html", {
                "request": request,
                "error": "Incorrect email or password",
                "email": user_credentials.email
            })
    
    if not user.is_active:
        if accepts_json(request):
            raise InactiveUserException(detail="Account is deactivated")
        else:
            return templates.TemplateResponse("pages/auth/login.html", {
                "request": request,
                "error": "Account is deactivated",
                "email": user_credentials.email
            })
    
    # Create proper JWT access token
    from ..utils.auth_utils import create_access_token
    from datetime import timedelta
    
    # Set token expiration based on remember_me
    if remember_me == "true":
        expires_delta = timedelta(days=30)  # 30 days if remember me is checked
    else:
        expires_delta = timedelta(hours=1)  # 1 hour default
    
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=expires_delta
    )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    if accepts_json(request):
        return {
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
    else:
        # For web browsers: set session cookie and redirect to dashboard
        response = RedirectResponse(url="/app/dashboard", status_code=303)
        
        # Set HTTP-only session cookie
        response.set_cookie(
            key="session_token",
            value=access_token,
            max_age=int(expires_delta.total_seconds()),
            httponly=True,  # Prevent XSS attacks
            secure=True if request.url.scheme == "https" else False,  # HTTPS only in production
            samesite="lax"  # CSRF protection
        )
        
        return response

@router.post("/logout", response_model=BaseResponse)
async def logout_user(request: Request):
    """Logout user (token invalidation)."""
    if accepts_json(request):
        return BaseResponse(message="Successfully logged out", success=True)
    else:
        # Clear session cookie and redirect to login
        response = RedirectResponse(url="/app/login?message=Successfully logged out", status_code=303)
        
        # Clear the session cookie
        response.delete_cookie(
            key="session_token",
            httponly=True,
            secure=True if request.url.scheme == "https" else False,
            samesite="lax"
        )
        
        return response 