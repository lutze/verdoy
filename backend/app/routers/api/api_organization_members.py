"""
API router for organization member management.

This module provides REST API endpoints for managing organization members,
invitations, and removal requests.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ...dependencies import get_db, get_current_user
from ...models.user import User
from ...services.organization_member_service import OrganizationMemberService
from ...services.organization_invitation_service import OrganizationInvitationService
from ...services.membership_removal_service import MembershipRemovalService
from ...schemas.organization import (
    OrganizationInviteCreate,
    OrganizationInviteResponse,
    OrganizationMemberResponse,
    OrganizationMemberListResponse
)

router = APIRouter(prefix="/api/organizations", tags=["Organization Members"])


@router.post("/{organization_id}/invite", response_model=OrganizationInviteResponse)
async def send_invitation(
    organization_id: UUID,
    invite_data: OrganizationInviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send an invitation to join an organization.
    
    Only organization admins can send invitations.
    """
    try:
        invitation_service = OrganizationInvitationService(db)
        invitation = invitation_service.send_invitation(
            organization_id=organization_id,
            email=invite_data.email,
            invited_by=current_user.id,
            role=invite_data.role,
            message=invite_data.message,
            expires_in_days=invite_data.expires_in_days
        )
        
        # Convert to response model
        return OrganizationInviteResponse(
            id=invitation.id,
            email=invitation.email,
            organization_id=invitation.organization_id,
            role=invitation.role,
            permissions=[],  # TODO: Implement permissions
            status=invitation.status,
            created_at=invitation.invited_at,
            expires_at=invitation.expires_at,
            accepted_at=invitation.accepted_at,
            organization_name=invitation.organization.name
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{organization_id}/invitations", response_model=List[OrganizationInviteResponse])
async def list_invitations(
    organization_id: UUID,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all invitations for an organization.
    
    Only organization admins can view invitations.
    """
    try:
        invitation_service = OrganizationInvitationService(db)
        invitations = invitation_service.get_organization_invitations(
            organization_id, status
        )
        
        return [
            OrganizationInviteResponse(
                id=invitation.id,
                email=invitation.email,
                organization_id=invitation.organization_id,
                role=invitation.role,
                permissions=[],  # TODO: Implement permissions
                status=invitation.status,
                created_at=invitation.invited_at,
                expires_at=invitation.expires_at,
                accepted_at=invitation.accepted_at,
                organization_name=invitation.organization.name
            )
            for invitation in invitations
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/invitations/{invitation_id}/accept")
async def accept_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an organization invitation.
    
    Users can only accept invitations sent to their email address.
    """
    try:
        invitation_service = OrganizationInvitationService(db)
        member = invitation_service.accept_invitation(
            invitation_id=invitation_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Invitation accepted successfully",
            "member_id": str(member.id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/invitations/{invitation_id}/decline")
async def decline_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decline an organization invitation.
    
    Users can only decline invitations sent to their email address.
    """
    try:
        invitation_service = OrganizationInvitationService(db)
        invitation = invitation_service.decline_invitation(
            invitation_id=invitation_id,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": "Invitation declined successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{organization_id}/members", response_model=OrganizationMemberListResponse)
async def list_members(
    organization_id: UUID,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all members of an organization.
    
    Only organization members can view the member list.
    """
    try:
        member_service = OrganizationMemberService(db)
        members = member_service.get_organization_members(
            organization_id, active_only
        )
        
        # Convert to response models
        member_responses = []
        for member in members:
            user = db.query(User).filter(User.id == member.user_id).first()
            member_responses.append(
                OrganizationMemberResponse(
                    id=member.id,
                    user_id=member.user_id,
                    organization_id=member.organization_id,
                    role=member.role,
                    permissions=[],  # TODO: Implement permissions
                    is_active=member.is_active,
                    joined_at=member.joined_at,
                    user_name=user.name if user else "Unknown",
                    user_email=user.email if user else "Unknown"
                )
            )
        
        return OrganizationMemberListResponse(
            members=member_responses,
            total=len(member_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{organization_id}/members/{user_id}/role")
async def update_member_role(
    organization_id: UUID,
    user_id: UUID,
    role: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a member's role in an organization.
    
    Only organization admins can update member roles.
    """
    try:
        member_service = OrganizationMemberService(db)
        member = member_service.update_member_role(
            organization_id=organization_id,
            user_id=user_id,
            new_role=role,
            updated_by=current_user.id
        )
        
        return {
            "success": True,
            "message": f"Member role updated to {role}",
            "member_id": str(member.id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{organization_id}/members/{user_id}/remove-request")
async def request_removal(
    organization_id: UUID,
    user_id: UUID,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request removal from an organization.
    
    Users can request their own removal, or admins can request removal of others.
    """
    try:
        removal_service = MembershipRemovalService(db)
        removal_request = removal_service.create_removal_request(
            organization_id=organization_id,
            user_id=user_id,
            requested_by=current_user.id,
            reason=reason
        )
        
        return {
            "success": True,
            "message": "Removal request created successfully",
            "request_id": str(removal_request.id)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{organization_id}/members/{user_id}/approve-removal")
async def approve_removal(
    organization_id: UUID,
    user_id: UUID,
    admin_notes: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a removal request.
    
    Only organization admins can approve removal requests.
    """
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No pending removal request found for this user"
            )
        
        removal_request = removal_service.approve_removal_request(
            request_id=removal_request.id,
            approved_by=current_user.id,
            admin_notes=admin_notes
        )
        
        return {
            "success": True,
            "message": "Removal request approved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{organization_id}/members/{user_id}")
async def remove_member(
    organization_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from an organization.
    
    Only organization admins can remove members.
    """
    try:
        member_service = OrganizationMemberService(db)
        success = member_service.remove_member(
            organization_id=organization_id,
            user_id=user_id,
            removed_by=current_user.id
        )
        
        return {
            "success": success,
            "message": "Member removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{organization_id}/removal-requests")
async def list_removal_requests(
    organization_id: UUID,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List removal requests for an organization.
    
    Only organization admins can view removal requests.
    """
    try:
        removal_service = MembershipRemovalService(db)
        requests = removal_service.get_organization_requests(organization_id, status)
        
        return {
            "requests": [
                {
                    "id": str(req.id),
                    "user_id": str(req.user_id),
                    "requested_by": str(req.requested_by),
                    "requested_at": req.requested_at,
                    "status": req.status,
                    "reason": req.reason,
                    "admin_notes": req.admin_notes
                }
                for req in requests
            ],
            "total": len(requests)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) 