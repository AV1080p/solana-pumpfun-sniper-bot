"""
OpenID Connect Service

Handles OIDC authentication and SSO.
"""
import os
import httpx
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from authlib.integrations.httpx_client import AsyncOAuth2Client

from models import User, OIDCProvider, AuthProvider, UserRole
from auth import create_access_token


class OIDCService:
    """Service for OpenID Connect authentication"""
    
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    async def get_authorization_url(
        self,
        provider_id: int,
        db: Session,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get OIDC authorization URL"""
        provider = db.query(OIDCProvider).filter(
            OIDCProvider.id == provider_id,
            OIDCProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OIDC provider not found or inactive"
            )
        
        redirect_uri = f"{self.base_url}/auth/oidc/{provider_id}/callback"
        
        # Use authlib to generate authorization URL
        client = AsyncOAuth2Client(
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            redirect_uri=redirect_uri
        )
        
        auth_url, state = client.create_authorization_url(
            url=provider.authorization_endpoint,
            scope=provider.scopes,
            state=state
        )
        
        return {
            "success": True,
            "authorization_url": auth_url,
            "state": state,
            "provider_id": provider_id,
            "provider_name": provider.name
        }
    
    async def handle_callback(
        self,
        provider_id: int,
        code: str,
        state: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Handle OIDC callback and authenticate user"""
        provider = db.query(OIDCProvider).filter(
            OIDCProvider.id == provider_id,
            OIDCProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OIDC provider not found"
            )
        
        redirect_uri = f"{self.base_url}/auth/oidc/{provider_id}/callback"
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                provider.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": provider.client_id,
                    "client_secret": provider.client_secret
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange authorization code"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            id_token = token_data.get("id_token")
            
            # Get user info
            userinfo_response = await client.get(
                provider.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get user information"
                )
            
            userinfo = userinfo_response.json()
            
            # Extract user attributes
            email = userinfo.get("email") or userinfo.get("sub")
            name = userinfo.get("name") or userinfo.get("given_name", "")
            sub = userinfo.get("sub")  # OIDC subject identifier
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not provided by OIDC provider"
                )
            
            # Find or create user
            user = db.query(User).filter(
                (User.email == email) |
                ((User.provider_id == sub) & (User.auth_provider == AuthProvider.OIDC))
            ).first()
            
            if user:
                # Update existing user
                user.provider_id = sub
                user.auth_provider = AuthProvider.OIDC
                user.full_name = name or user.full_name
                user.last_login = datetime.utcnow()
                if not user.is_verified:
                    user.is_verified = True
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=name,
                    auth_provider=AuthProvider.OIDC,
                    provider_id=sub,
                    is_active=True,
                    is_verified=True,
                    role=UserRole.USER
                )
                db.add(user)
            
            db.commit()
            db.refresh(user)
            
            # Create access token
            jwt_token = create_access_token(data={"sub": user.id, "email": user.email})
            
            return {
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role.value,
                    "avatar_url": user.avatar_url
                },
                "access_token": jwt_token,
                "token_type": "bearer"
            }
    
    async def get_provider_info(
        self,
        provider_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Get OIDC provider information"""
        provider = db.query(OIDCProvider).filter(
            OIDCProvider.id == provider_id
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OIDC provider not found"
            )
        
        return {
            "id": provider.id,
            "name": provider.name,
            "issuer": provider.issuer,
            "scopes": provider.scopes,
            "is_active": provider.is_active
        }

