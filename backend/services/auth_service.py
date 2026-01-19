"""
Authentication Service

Handles OAuth2 authentication with multiple providers (Google, GitHub, etc.)
and traditional email/password authentication.
"""
import os
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import User, AuthProvider, UserRole
from auth import get_password_hash, verify_password, create_access_token
from datetime import datetime


class AuthService:
    """Service for handling authentication operations"""

    def __init__(self):
        # OAuth2 Configuration
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
        self.facebook_client_id = os.getenv("FACEBOOK_CLIENT_ID")
        self.facebook_client_secret = os.getenv("FACEBOOK_CLIENT_SECRET")
        self.apple_client_id = os.getenv("APPLE_CLIENT_ID")
        self.apple_client_secret = os.getenv("APPLE_CLIENT_SECRET")
        
        # OAuth redirect URLs
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    async def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Register a new user with email/password"""
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check username if provided
        if username:
            existing_username = db.query(User).filter(User.username == username).first()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Create new user
        hashed_password = get_password_hash(password)
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=hashed_password,
            auth_provider=AuthProvider.EMAIL,
            is_active=True,
            is_verified=False,  # Email verification can be added later
            role=UserRole.USER
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create access token
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
            "token_type": "bearer"
        }

    async def login_user(
        self,
        email: str,
        password: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Authenticate user with email/password"""
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Check if user has password (OAuth users might not have one)
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account uses social login. Please sign in with your provider."
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id, "email": user.email})
        
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
            "access_token": access_token,
            "token_type": "bearer"
        }

    async def verify_google_token(self, token: str, db: Session) -> Dict[str, Any]:
        """Verify Google OAuth token and create/update user"""
        try:
            async with httpx.AsyncClient() as client:
                # Verify token with Google
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google token"
                    )
                
                google_user = response.json()
                
                # Check if user exists by email or provider_id
                user = db.query(User).filter(
                    (User.email == google_user["email"]) |
                    ((User.provider_id == google_user["id"]) & (User.auth_provider == AuthProvider.GOOGLE))
                ).first()
                
                if user:
                    # Update existing user
                    user.provider_id = google_user["id"]
                    user.auth_provider = AuthProvider.GOOGLE
                    user.avatar_url = google_user.get("picture")
                    user.full_name = google_user.get("name")
                    user.last_login = datetime.utcnow()
                    if not user.is_verified:
                        user.is_verified = True
                else:
                    # Create new user
                    user = User(
                        email=google_user["email"],
                        full_name=google_user.get("name"),
                        auth_provider=AuthProvider.GOOGLE,
                        provider_id=google_user["id"],
                        avatar_url=google_user.get("picture"),
                        is_active=True,
                        is_verified=True,
                        role=UserRole.USER
                    )
                    db.add(user)
                
                db.commit()
                db.refresh(user)
                
                # Create access token
                access_token = create_access_token(data={"sub": user.id, "email": user.email})
                
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
                    "access_token": access_token,
                    "token_type": "bearer"
                }
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to verify Google token: {str(e)}"
            )

    async def verify_github_token(self, token: str, db: Session) -> Dict[str, Any]:
        """Verify GitHub OAuth token and create/update user"""
        try:
            async with httpx.AsyncClient() as client:
                # Get user info from GitHub
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {token}"}
                )
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid GitHub token"
                    )
                
                github_user = response.json()
                
                # Get email if not public
                email = github_user.get("email")
                if not email:
                    email_response = await client.get(
                        "https://api.github.com/user/emails",
                        headers={"Authorization": f"token {token}"}
                    )
                    if email_response.status_code == 200:
                        emails = email_response.json()
                        email = next((e["email"] for e in emails if e.get("primary")), emails[0]["email"] if emails else None)
                
                if not email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="GitHub account email not available"
                    )
                
                # Check if user exists
                user = db.query(User).filter(
                    (User.email == email) |
                    ((User.provider_id == str(github_user["id"])) & (User.auth_provider == AuthProvider.GITHUB))
                ).first()
                
                if user:
                    user.provider_id = str(github_user["id"])
                    user.auth_provider = AuthProvider.GITHUB
                    user.avatar_url = github_user.get("avatar_url")
                    user.full_name = github_user.get("name")
                    user.last_login = datetime.utcnow()
                    if not user.is_verified:
                        user.is_verified = True
                else:
                    user = User(
                        email=email,
                        username=github_user.get("login"),
                        full_name=github_user.get("name"),
                        auth_provider=AuthProvider.GITHUB,
                        provider_id=str(github_user["id"]),
                        avatar_url=github_user.get("avatar_url"),
                        is_active=True,
                        is_verified=True,
                        role=UserRole.USER
                    )
                    db.add(user)
                
                db.commit()
                db.refresh(user)
                
                access_token = create_access_token(data={"sub": user.id, "email": user.email})
                
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
                    "access_token": access_token,
                    "token_type": "bearer"
                }
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to verify GitHub token: {str(e)}"
            )

    def get_oauth_url(self, provider: str) -> Dict[str, str]:
        """Get OAuth authorization URL for a provider"""
        if provider.lower() == "google":
            if not self.google_client_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Google OAuth not configured"
                )
            redirect_uri = f"{self.base_url}/auth/google/callback"
            scope = "openid email profile"
            url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={self.google_client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"access_type=offline&"
                f"prompt=consent"
            )
            return {"url": url, "provider": "google"}
        
        elif provider.lower() == "github":
            if not self.github_client_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GitHub OAuth not configured"
                )
            redirect_uri = f"{self.base_url}/auth/github/callback"
            scope = "user:email"
            url = (
                f"https://github.com/login/oauth/authorize?"
                f"client_id={self.github_client_id}&"
                f"redirect_uri={redirect_uri}&"
                f"scope={scope}"
            )
            return {"url": url, "provider": "github"}
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

    async def handle_oauth_callback(
        self,
        provider: str,
        code: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for token"""
        if provider.lower() == "google":
            return await self._handle_google_callback(code, db)
        elif provider.lower() == "github":
            return await self._handle_github_callback(code, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )

    async def _handle_google_callback(self, code: str, db: Session) -> Dict[str, Any]:
        """Handle Google OAuth callback"""
        redirect_uri = f"{self.base_url}/auth/google/callback"
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": self.google_client_id,
                    "client_secret": self.google_client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange Google authorization code"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Verify token and get user info
            return await self.verify_google_token(access_token, db)

    async def _handle_github_callback(self, code: str, db: Session) -> Dict[str, Any]:
        """Handle GitHub OAuth callback"""
        redirect_uri = f"{self.base_url}/auth/github/callback"
        
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "code": code,
                    "client_id": self.github_client_id,
                    "client_secret": self.github_client_secret,
                    "redirect_uri": redirect_uri
                },
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to exchange GitHub authorization code"
                )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to get access token from GitHub"
                )
            
            # Verify token and get user info
            return await self.verify_github_token(access_token, db)

