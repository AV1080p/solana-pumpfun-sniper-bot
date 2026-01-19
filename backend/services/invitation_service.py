"""
Invitation Service

Handles user invitations and onboarding workflows.
"""
import os
import secrets
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from models import User, Invitation, InvitationStatus, UserRole, AuthProvider
from auth import get_password_hash


class InvitationService:
    """Service for managing user invitations"""
    
    def __init__(self):
        self.invitation_expiry_days = int(os.getenv("INVITATION_EXPIRY_DAYS", "7"))
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def generate_invitation_token(self) -> str:
        """Generate a secure invitation token"""
        return secrets.token_urlsafe(32)
    
    async def create_invitation(
        self,
        email: str,
        invited_by: User,
        role: UserRole = UserRole.USER,
        metadata: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new invitation"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Check for pending invitation
        pending_invitation = db.query(Invitation).filter(
            Invitation.email == email,
            Invitation.status == InvitationStatus.PENDING,
            Invitation.expires_at > datetime.utcnow()
        ).first()
        
        if pending_invitation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pending invitation already exists for this email"
            )
        
        # Create invitation
        token = self.generate_invitation_token()
        expires_at = datetime.utcnow() + timedelta(days=self.invitation_expiry_days)
        
        invitation = Invitation(
            email=email,
            token=token,
            invited_by=invited_by.id,
            role=role,
            status=InvitationStatus.PENDING,
            expires_at=expires_at,
            metadata=str(metadata) if metadata else None
        )
        
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        
        # Generate invitation URL
        invitation_url = f"{self.frontend_url}/auth/accept-invitation?token={token}"
        
        return {
            "success": True,
            "invitation": {
                "id": invitation.id,
                "email": invitation.email,
                "token": invitation.token,
                "role": invitation.role.value,
                "expires_at": invitation.expires_at.isoformat(),
                "invitation_url": invitation_url
            },
            "message": "Invitation created successfully"
        }
    
    async def get_invitation_by_token(
        self,
        token: str,
        db: Session
    ) -> Invitation:
        """Get invitation by token"""
        invitation = db.query(Invitation).filter(
            Invitation.token == token
        ).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invitation token"
            )
        
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation has been {invitation.status.value}"
            )
        
        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )
        
        return invitation
    
    async def accept_invitation(
        self,
        token: str,
        password: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Accept an invitation and create user account"""
        invitation = await self.get_invitation_by_token(token, db)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == invitation.email).first()
        if existing_user:
            invitation.status = InvitationStatus.CANCELLED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create user
        hashed_password = get_password_hash(password)
        user = User(
            email=invitation.email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            auth_provider=AuthProvider.EMAIL,
            role=invitation.role,
            is_active=True,
            is_verified=True  # Invited users are pre-verified
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by_user_id = user.id
        db.commit()
        
        # Create access token
        from auth import create_access_token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role.value
            },
            "access_token": access_token,
            "token_type": "bearer",
            "message": "Account created successfully"
        }
    
    async def cancel_invitation(
        self,
        invitation_id: int,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Cancel an invitation (only by inviter or admin)"""
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        # Check permissions
        if invitation.invited_by != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel invitations you created"
            )
        
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel {invitation.status.value} invitation"
            )
        
        invitation.status = InvitationStatus.CANCELLED
        db.commit()
        
        return {
            "success": True,
            "message": "Invitation cancelled successfully"
        }
    
    async def list_invitations(
        self,
        user: Optional[User] = None,
        status_filter: Optional[InvitationStatus] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """List invitations"""
        query = db.query(Invitation)
        
        if user and user.role != UserRole.ADMIN:
            # Non-admins can only see their own invitations
            query = query.filter(Invitation.invited_by == user.id)
        
        if status_filter:
            query = query.filter(Invitation.status == status_filter)
        
        invitations = query.order_by(Invitation.created_at.desc()).all()
        
        return [
            {
                "id": inv.id,
                "email": inv.email,
                "role": inv.role.value,
                "status": inv.status.value,
                "expires_at": inv.expires_at.isoformat(),
                "accepted_at": inv.accepted_at.isoformat() if inv.accepted_at else None,
                "created_at": inv.created_at.isoformat()
            }
            for inv in invitations
        ]
    
    async def resend_invitation(
        self,
        invitation_id: int,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Resend an invitation (regenerate token and extend expiry)"""
        invitation = db.query(Invitation).filter(Invitation.id == invitation_id).first()
        
        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        # Check permissions
        if invitation.invited_by != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only resend invitations you created"
            )
        
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resend {invitation.status.value} invitation"
            )
        
        # Regenerate token and extend expiry
        invitation.token = self.generate_invitation_token()
        invitation.expires_at = datetime.utcnow() + timedelta(days=self.invitation_expiry_days)
        db.commit()
        
        invitation_url = f"{self.frontend_url}/auth/accept-invitation?token={invitation.token}"
        
        return {
            "success": True,
            "invitation": {
                "id": invitation.id,
                "email": invitation.email,
                "token": invitation.token,
                "expires_at": invitation.expires_at.isoformat(),
                "invitation_url": invitation_url
            },
            "message": "Invitation resent successfully"
        }

