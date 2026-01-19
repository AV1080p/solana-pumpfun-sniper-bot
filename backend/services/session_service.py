"""
Session Management Service

Handles user sessions, refresh tokens, and device tracking.
"""
import os
import secrets
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from models import User, UserSession, SessionStatus
from auth import create_access_token, decode_access_token


class SessionService:
    """Service for managing user sessions"""
    
    def __init__(self):
        self.session_expiry_hours = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
        self.refresh_token_expiry_days = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "30"))
        self.max_sessions_per_user = int(os.getenv("MAX_SESSIONS_PER_USER", "10"))
    
    def generate_session_token(self) -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    def generate_refresh_token(self) -> str:
        """Generate a secure refresh token"""
        return secrets.token_urlsafe(32)
    
    async def create_session(
        self,
        user: User,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new user session"""
        # Check session limit
        active_sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.status == SessionStatus.ACTIVE
        ).count()
        
        if active_sessions >= self.max_sessions_per_user:
            # Revoke oldest session
            oldest_session = db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.status == SessionStatus.ACTIVE
            ).order_by(UserSession.created_at.asc()).first()
            
            if oldest_session:
                oldest_session.status = SessionStatus.REVOKED
                db.commit()
        
        # Generate tokens
        session_token = self.generate_session_token()
        refresh_token = self.generate_refresh_token()
        
        # Create session
        expires_at = datetime.utcnow() + timedelta(hours=self.session_expiry_hours)
        refresh_expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expiry_days)
        
        session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE,
            expires_at=expires_at
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "session_id": session.id}
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "refresh_expires_at": refresh_expires_at.isoformat(),
            "session_id": session.id
        }
    
    async def refresh_session(
        self,
        refresh_token: str,
        db: Session
    ) -> Dict[str, Any]:
        """Refresh an access token using refresh token"""
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.status == SessionStatus.ACTIVE
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if session expired
        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired"
            )
        
        # Get user
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or not user.is_active:
            session.status = SessionStatus.REVOKED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive"
            )
        
        # Update session
        session.last_activity = datetime.utcnow()
        session.expires_at = datetime.utcnow() + timedelta(hours=self.session_expiry_hours)
        db.commit()
        
        # Create new access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "session_id": session.id}
        )
        
        return {
            "success": True,
            "access_token": access_token,
            "expires_at": session.expires_at.isoformat()
        }
    
    async def revoke_session(
        self,
        session_id: Optional[int] = None,
        session_token: Optional[str] = None,
        user: Optional[User] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Revoke a session"""
        if session_id:
            session = db.query(UserSession).filter(UserSession.id == session_id).first()
        elif session_token:
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="session_id or session_token required"
            )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Check if user owns the session
        if user and session.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revoke your own sessions"
            )
        
        session.status = SessionStatus.REVOKED
        db.commit()
        
        return {
            "success": True,
            "message": "Session revoked successfully"
        }
    
    async def revoke_all_sessions(
        self,
        user: User,
        db: Session,
        keep_current: bool = True,
        current_session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Revoke all sessions for a user"""
        query = db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.status == SessionStatus.ACTIVE
        )
        
        if keep_current and current_session_id:
            query = query.filter(UserSession.id != current_session_id)
        
        sessions = query.all()
        for session in sessions:
            session.status = SessionStatus.REVOKED
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Revoked {len(sessions)} session(s)",
            "revoked_count": len(sessions)
        }
    
    async def get_user_sessions(
        self,
        user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""
        sessions = db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).order_by(UserSession.created_at.desc()).all()
        
        return [
            {
                "id": session.id,
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "is_current": False  # Will be set by caller if needed
            }
            for session in sessions
        ]
    
    async def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions"""
        expired_sessions = db.query(UserSession).filter(
            UserSession.status == SessionStatus.ACTIVE,
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            session.status = SessionStatus.EXPIRED
        
        db.commit()
        return count
    
    async def get_session_by_token(
        self,
        session_token: str,
        db: Session
    ) -> Optional[UserSession]:
        """Get session by token"""
        return db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.status == SessionStatus.ACTIVE
        ).first()

