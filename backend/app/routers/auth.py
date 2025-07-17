"""
Authentication router for user registration, login, and token management.

This router handles all authentication-related operations including:
- User registration and account creation
- User login and token generation
- Token refresh and validation
- Password reset functionality
- User profile management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.security import HTTPBearer
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

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

router = APIRouter(tags=["Authentication"])

# Templates configuration
templates = Jinja2Templates(directory="app/templates")

def accepts_json(request: Request) -> bool:
    """Check if client prefers JSON responses"""
    accept_header = request.headers.get("accept", "")
    return (
        "application/json" in accept_header or
        "application/ld+json" in accept_header or
        request.url.path.startswith("/api/")
    )

# ============================================================================
# HTML PAGES (GET ROUTES)
# ============================================================================

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Display login page for web browsers."""
    return templates.TemplateResponse("pages/auth/login.html", {
        "request": request,
        "error": error,
        "message": message
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Display registration page for web browsers."""
    # Get available organizations for the dropdown (simplified for now)
    organizations = []  # TODO: Implement organization loading
    
    return templates.TemplateResponse("pages/auth/register.html", {
        "request": request,
        "organizations": organizations
    })

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Display user profile page for web browsers."""
    # Simplified for now - TODO: Add authentication
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
    accept_terms: Optional[str] = Form(None),
    # JSON data for API calls
    user_data: Optional[UserCreate] = None
):
    """Register a new user account with both HTML and JSON support."""
    # Handle form data vs JSON data
    if user_data is None:
        # This is a form submission
        if not all([name, email, password]):
            if accepts_json(request):
                raise HTTPException(status_code=400, detail="Missing required fields")
            else:
                return templates.TemplateResponse("pages/auth/register.html", {
                    "request": request,
                    "error": "All fields are required",
                    "name": name,
                    "email": email,
                    "organizations": []
                })
        
        user_data = UserCreate(
            name=name,
            email=email,
            password=password,
            organization_id=organization_id
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        if accepts_json(request):
            raise UserAlreadyExistsException(detail="Email already registered")
        else:
            return templates.TemplateResponse("pages/auth/register.html", {
                "request": request,
                "error": "Email already registered",
                "name": user_data.name,
                "email": user_data.email,
                "organizations": []
            })
    
    # Create user with hashed password
    hashed_password = User.hash_password(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True
    )
    
    # TODO: Create associated entity for user profile
    # For now, just create the user
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Return response based on content type
    if accepts_json(request):
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user_data.name,
            organization_id=user_data.organization_id,
            is_active=user.is_active,
            created_at=user.created_at
        )
    else:
        # Redirect to login with success message
        return RedirectResponse(
            url="/api/v1/auth/login?message=Account created successfully! Please sign in.",
            status_code=303
        )

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
    remember_me: Optional[str] = Form(None),
    # JSON data for API calls
    user_credentials: Optional[UserLogin] = None
):
    """Authenticate user with both HTML and JSON support."""
    # Handle form data vs JSON data
    if user_credentials is None:
        if not email or not password:
            if accepts_json(request):
                raise HTTPException(status_code=400, detail="Email and password required")
            else:
                return templates.TemplateResponse("pages/auth/login.html", {
                    "request": request,
                    "error": "Email and password are required",
                    "email": email
                })
        
        user_credentials = UserLogin(email=email, password=password)
    
    # Verify user credentials
    user = db.query(User).filter(User.email == user_credentials.email).first()
    if not user or not user.verify_password(user_credentials.password):
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
    
    # Create access token (simplified for now)
    # TODO: Implement proper JWT token creation
    if accepts_json(request):
        return {
            "access_token": "dummy_token",
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": "User Name",
                "is_active": user.is_active
            }
        }
    else:
        # Redirect to dashboard (or profile for now)
        return RedirectResponse(url="/api/v1/auth/profile", status_code=303)

@router.post("/logout", response_model=BaseResponse)
async def logout_user(request: Request):
    """Logout user (token invalidation)."""
    if accepts_json(request):
        return BaseResponse(message="Successfully logged out", success=True)
    else:
        # Clear cookie and redirect to login
        response = RedirectResponse(url="/api/v1/auth/login?message=Successfully logged out", status_code=303)
        # TODO: Clear authentication cookie
        return response 