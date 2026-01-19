"""
SAML 2.0 Service

Handles SAML authentication and SSO.
"""
import os
import base64
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from models import User, SAMLProvider, AuthProvider, UserRole
from auth import create_access_token

try:
    from onelogin.saml2.auth import OneLogin_Saml2_Auth
    from onelogin.saml2.settings import OneLogin_Saml2_Settings
    from onelogin.saml2.utils import OneLogin_Saml2_Utils
    SAML_AVAILABLE = True
except ImportError:
    SAML_AVAILABLE = False


class SAMLService:
    """Service for SAML 2.0 authentication"""
    
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    def _prepare_saml_request(self, request, provider: SAMLProvider) -> Dict[str, Any]:
        """Prepare SAML request data"""
        return {
            'https': 'on' if request.url.scheme == 'https' else 'off',
            'http_host': request.url.hostname,
            'script_name': request.url.path,
            'server_port': request.url.port or (443 if request.url.scheme == 'https' else 80),
            'get_data': dict(request.query_params),
            'post_data': {}
        }
    
    async def initiate_sso(
        self,
        provider_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Initiate SAML SSO"""
        if not SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SAML library not available. Install python3-saml."
            )
        
        provider = db.query(SAMLProvider).filter(
            SAMLProvider.id == provider_id,
            SAMLProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SAML provider not found or inactive"
            )
        
        # Build SAML settings
        settings = {
            'sp': {
                'entityId': f"{self.base_url}/saml/metadata/{provider_id}",
                'assertionConsumerService': {
                    'url': f"{self.base_url}/saml/acs/{provider_id}",
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST'
                },
                'singleLogoutService': {
                    'url': f"{self.base_url}/saml/sls/{provider_id}",
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                },
                'NameIDFormat': 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
                'x509cert': provider.x509_cert,
                'privateKey': ''  # SP private key if needed
            },
            'idp': {
                'entityId': provider.entity_id,
                'singleSignOnService': {
                    'url': provider.sso_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                },
                'singleLogoutService': {
                    'url': provider.slo_url,
                    'binding': 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect'
                } if provider.slo_url else None,
                'x509cert': provider.x509_cert
            }
        }
        
        saml_settings = OneLogin_Saml2_Settings(settings=settings)
        auth = OneLogin_Saml2_Auth({}, saml_settings)
        
        # Generate SSO URL
        sso_url = auth.login(return_to=f"{self.frontend_url}/auth/saml/callback")
        
        return {
            "success": True,
            "sso_url": sso_url,
            "provider_id": provider_id,
            "provider_name": provider.name
        }
    
    async def process_assertion(
        self,
        provider_id: int,
        saml_response: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process SAML assertion and authenticate user"""
        if not SAML_AVAILABLE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SAML library not available"
            )
        
        provider = db.query(SAMLProvider).filter(
            SAMLProvider.id == provider_id,
            SAMLProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SAML provider not found"
            )
        
        # Process SAML response
        # This is a simplified version - full implementation would need proper request handling
        # In production, you'd parse the SAMLResponse from the POST request
        
        # For now, return a placeholder
        # In real implementation, you would:
        # 1. Parse SAML response
        # 2. Extract user attributes (email, name, etc.)
        # 3. Create or update user
        # 4. Generate JWT token
        
        return {
            "success": False,
            "message": "SAML assertion processing not fully implemented. Requires proper SAML response parsing."
        }
    
    async def get_metadata(
        self,
        provider_id: int,
        db: Session
    ) -> str:
        """Get SAML metadata for service provider"""
        provider = db.query(SAMLProvider).filter(
            SAMLProvider.id == provider_id,
            SAMLProvider.is_active == True
        ).first()
        
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SAML provider not found"
            )
        
        # Generate SP metadata XML
        # This would be generated from SAML settings
        metadata_xml = f"""<?xml version="1.0"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata"
                  entityID="{self.base_url}/saml/metadata/{provider_id}">
    <SPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <NameIDFormat>urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress</NameIDFormat>
        <AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                  Location="{self.base_url}/saml/acs/{provider_id}"
                                  index="0"/>
    </SPSSODescriptor>
</EntityDescriptor>"""
        
        return metadata_xml

