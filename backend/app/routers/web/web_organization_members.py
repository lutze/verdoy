"""
Web router for organization member management.

This module provides HTML-based endpoints for managing organization members,
invitations, and removal requests through the web interface.
"""

from fastapi import APIRouter, Depends, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from ...dependencies import get_db, get_web_user
from ...models.user import User
from ...models.organization_member import OrganizationMember
from ...models.entity import Entity
from ...services.organization_member_service import OrganizationMemberService
from ...services.organization_invitation_service import OrganizationInvitationService
from ...services.membership_removal_service import MembershipRemovalService
from ...templates_config import templates

router = APIRouter(prefix="/app/admin/organization", tags=["Web Organization Members"])


@router.get("/{organization_id}/members", response_class=HTMLResponse, include_in_schema=False)
async def organization_members_page(
    request: Request,
    organization_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Organization members management page."""
    try:
        member_service = OrganizationMemberService(db)
        invitation_service = OrganizationInvitationService(db)
        removal_service = MembershipRemovalService(db)
        
        # Get organization details
        from ...services.organization_service import OrganizationService
        org_service = OrganizationService(db)
        organization = org_service.get_by_id(organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Get members
        members = member_service.get_organization_members(organization_id, active_only=True)
        
        # Load user data for each member
        for member in members:
            user_entity = db.query(Entity).filter(Entity.id == member.user_id, Entity.entity_type == 'user').first()
            if user_entity:
                member.user = User()
                member.user.id = user_entity.id
                member.user.name = user_entity.name
                member.user.email = user_entity.get_property('email', '')
                member.user.is_superuser = user_entity.get_property('is_superuser', False)
            else:
                member.user = None
        
        # Get pending invitations
        invitations = invitation_service.get_organization_invitations(organization_id, status="pending")
        
        # Get pending removal requests
        removal_requests = removal_service.get_pending_requests(organization_id)
        
        # Get current user's membership
        current_user_member = member_service.get_member(organization_id, current_user.id)
        
        return templates.TemplateResponse(
            "pages/organizations/members.html",
            {
                "request": request,
                "organization": organization,
                "members": members,
                "invitations": invitations,
                "removal_requests": removal_requests,
                "current_user": current_user,
                "current_user_member": current_user_member,
                "page_title": f"Members - {organization.name}"
            }
        )
        
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in organization_members_page: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error": str(e),
                "current_user": current_user,
                "page_title": "Error"
            },
            status_code=500
        )


@router.post("/{organization_id}/invite", response_class=HTMLResponse, include_in_schema=False)
async def send_invitation(
    request: Request,
    organization_id: UUID,
    email: str = Form(...),
    role: str = Form("member"),
    message: Optional[str] = Form(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Send an invitation to join the organization."""
    try:
        invitation_service = OrganizationInvitationService(db)
        invitation = invitation_service.send_invitation(
            organization_id=organization_id,
            email=email,
            invited_by=current_user.id,
            role=role,
            message=message,
            expires_in_days=7
        )
        
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?success=invitation_sent",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?error={str(e)}",
            status_code=302
        )


@router.post("/{organization_id}/members/{user_id}/role", response_class=HTMLResponse, include_in_schema=False)
async def update_member_role(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    role: str = Form(...),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Update a member's role."""
    try:
        member_service = OrganizationMemberService(db)
        member = member_service.update_member_role(
            organization_id=organization_id,
            user_id=user_id,
            new_role=role,
            updated_by=current_user.id
        )
        
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?success=role_updated",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?error={str(e)}",
            status_code=302
        )


@router.post("/{organization_id}/members/{user_id}/remove", response_class=HTMLResponse, include_in_schema=False)
async def remove_member(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Remove a member from the organization."""
    try:
        member_service = OrganizationMemberService(db)
        success = member_service.remove_member(
            organization_id=organization_id,
            user_id=user_id,
            removed_by=current_user.id
        )
        
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?success=member_removed",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?error={str(e)}",
            status_code=302
        )


@router.post("/{organization_id}/members/{user_id}/request-removal", response_class=HTMLResponse, include_in_schema=False)
async def request_removal(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    reason: Optional[str] = Form(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Request removal from the organization."""
    try:
        removal_service = MembershipRemovalService(db)
        removal_request = removal_service.create_removal_request(
            organization_id=organization_id,
            user_id=user_id,
            requested_by=current_user.id,
            reason=reason
        )
        
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?success=removal_requested",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?error={str(e)}",
            status_code=302
        )


@router.post("/{organization_id}/members/{user_id}/approve-removal", response_class=HTMLResponse, include_in_schema=False)
async def approve_removal(
    request: Request,
    organization_id: UUID,
    user_id: UUID,
    admin_notes: Optional[str] = Form(None),
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Approve a removal request."""
    try:
        removal_service = MembershipRemovalService(db)
        
        # Find the pending removal request
        requests = removal_service.get_organization_requests(organization_id, status="pending")
        removal_request = None
        for req in requests:
            if req.user_id == user_id:
                removal_request = req
                break
        
        if not removal_request:
            raise Exception("No pending removal request found for this user")
        
        removal_request = removal_service.approve_removal_request(
            request_id=removal_request.id,
            approved_by=current_user.id,
            admin_notes=admin_notes
        )
        
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?success=removal_approved",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/admin/organization/{organization_id}/members?error={str(e)}",
            status_code=302
        )


@router.get("/invitations/{invitation_id}", response_class=HTMLResponse, include_in_schema=False)
async def invitation_page(
    request: Request,
    invitation_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Invitation acceptance/decline page."""
    try:
        invitation_service = OrganizationInvitationService(db)
        invitation = invitation_service.get_invitation(invitation_id)
        
        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")
        
        # Check if invitation is for current user
        if invitation.email != current_user.email:
            raise HTTPException(status_code=403, detail="This invitation is not for you")
        
        # Get organization details
        from ...services.organization_service import OrganizationService
        org_service = OrganizationService(db)
        organization = org_service.get_by_id(invitation.organization_id)
        
        return templates.TemplateResponse(
            "pages/organizations/invitation.html",
            {
                "request": request,
                "invitation": invitation,
                "organization": organization,
                "current_user": current_user,
                "page_title": f"Organization Invitation - {organization.name}"
            }
        )
        
    except Exception as e:
        return templates.TemplateResponse(
            "pages/error.html",
            {
                "request": request,
                "error": str(e),
                "current_user": current_user,
                "page_title": "Error"
            }
        )


@router.post("/invitations/{invitation_id}/accept", response_class=HTMLResponse, include_in_schema=False)
async def accept_invitation(
    request: Request,
    invitation_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Accept an organization invitation."""
    try:
        invitation_service = OrganizationInvitationService(db)
        member = invitation_service.accept_invitation(
            invitation_id=invitation_id,
            user_id=current_user.id
        )
        
        return RedirectResponse(
            url=f"/app/dashboard?success=invitation_accepted",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/invitations/{invitation_id}?error={str(e)}",
            status_code=302
        )


@router.post("/invitations/{invitation_id}/decline", response_class=HTMLResponse, include_in_schema=False)
async def decline_invitation(
    request: Request,
    invitation_id: UUID,
    current_user: User = Depends(get_web_user),
    db: Session = Depends(get_db)
):
    """Decline an organization invitation."""
    try:
        invitation_service = OrganizationInvitationService(db)
        invitation = invitation_service.decline_invitation(
            invitation_id=invitation_id,
            user_id=current_user.id
        )
        
        return RedirectResponse(
            url=f"/app/dashboard?success=invitation_declined",
            status_code=302
        )
        
    except Exception as e:
        return RedirectResponse(
            url=f"/app/invitations/{invitation_id}?error={str(e)}",
            status_code=302
        ) 