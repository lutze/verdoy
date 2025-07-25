"""
Web-only authentication router for /app/auth endpoints.
Handles all HTML-based authentication for web browser clients (session/cookie auth).
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import timedelta, datetime

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...services.auth_service import AuthService
from ...templates_config import templates

router = APIRouter(prefix="/app/auth", tags=["Web Authentication"])

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    """Display login page for web browsers."""
    return templates.TemplateResponse("pages/auth/login.html", {
        "request": request,
        "error": error,
        "message": message
    })

@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_user(
    request: Request,
    db: Session = Depends(get_db),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    remember_me: Optional[str] = Form(None)
):
    """Authenticate user with form data and set session cookie."""
    if not email or not password:
        return templates.TemplateResponse("pages/auth/login.html", {
            "request": request,
            "error": "Email and password are required",
            "email": email
        })
    auth_service = AuthService(db)
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.check_password(password):
        return templates.TemplateResponse("pages/auth/login.html", {
            "request": request,
            "error": "Incorrect email or password",
            "email": email
        })
    if not user.is_active:
        return templates.TemplateResponse("pages/auth/login.html", {
            "request": request,
            "error": "Account is deactivated",
            "email": email
        })
    from ...utils.auth_utils import create_access_token
    if remember_me == "true":
        expires_delta = timedelta(days=30)
    else:
        expires_delta = timedelta(hours=1)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=expires_delta
    )
    user.last_login = datetime.utcnow()
    db.commit()
    response = RedirectResponse(url="/app/dashboard", status_code=303)
    response.set_cookie(
        key="session_token",
        value=access_token,
        max_age=int(expires_delta.total_seconds()),
        httponly=True,
        secure=True if request.url.scheme == "https" else False,
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_page(request: Request, db: Session = Depends(get_db)):
    """Display registration page for web browsers."""
    organizations = []  # TODO: Implement organization loading
    return templates.TemplateResponse("pages/auth/register.html", {
        "request": request,
        "organizations": organizations
    })

@router.post("/register", response_class=HTMLResponse, include_in_schema=False)
async def register_user(
    request: Request,
    db: Session = Depends(get_db),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    organization_id: Optional[str] = Form(None),
    new_organization_name: Optional[str] = Form(None),
    accept_terms: Optional[str] = Form(None)
):
    """Register a new user account via HTML form."""
    if not all([name, email, password]):
        return templates.TemplateResponse("pages/auth/register.html", {
            "request": request,
            "error": "All fields are required",
            "name": name,
            "email": email,
            "organizations": []
        })
    # Handle organization creation/assignment as in original logic
    from ...schemas.user import UserCreate
    from ...services.organization_service import OrganizationService
    from ...schemas.organization import OrganizationCreate
    import uuid
    auth_service = AuthService(db)
    org_service = OrganizationService(db)
    org_id = None
    if organization_id and organization_id != "create_new":
        try:
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
    try:
        user = auth_service.register_user(user_data)
        final_organization_id = None
        if organization_id == "create_new" and new_organization_name:
            org_data = OrganizationCreate(
                name=new_organization_name,
                description=f"Organization created by {name}",
                organization_type="small_business"
            )
            organization = org_service.create_organization(org_data, user.id)
            if user.entity:
                user.entity.organization_id = organization.id
                db.commit()
                final_organization_id = organization.id
        elif org_id:
            if user.entity:
                user.entity.organization_id = org_id
                db.commit()
                final_organization_id = org_id
        return RedirectResponse(
            url="/app/auth/login?message=Account created successfully! Please sign in.",
            status_code=303
        )
    except Exception as e:
        return templates.TemplateResponse("pages/auth/register.html", {
            "request": request,
            "error": "Registration failed. Please try again.",
            "name": name,
            "email": email,
            "organizations": []
        })

@router.post("/logout", response_class=HTMLResponse, include_in_schema=False)
async def logout_user(request: Request):
    """Logout user (clear session cookie and redirect)."""
    response = RedirectResponse(url="/app/auth/login?message=Successfully logged out", status_code=303)
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=True if request.url.scheme == "https" else False,
        samesite="lax"
    )
    return response

@router.get("/admin/profile", response_class=HTMLResponse, include_in_schema=False)
async def profile_page(request: Request, current_user: User = Depends(get_web_user)):
    """Display user profile page for web browsers."""
    # TODO: Implement actual user/profile loading
    return templates.TemplateResponse("pages/auth/profile.html", {
        "request": request,
        "user": {"name": current_user.entity.name if current_user.entity else current_user.email, "email": current_user.email},
        "organization": current_user.entity.organization_id if current_user.entity else None,
        "api_keys": []
    }) 