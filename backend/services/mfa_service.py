"""
Multi-Factor Authentication Service

Handles TOTP, SMS, and backup codes for MFA.
"""
import os
import pyotp
import qrcode
import io
import base64
import secrets
import json
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta

from models import User, MFADevice, MFAMethod


class MFAService:
    """Service for managing multi-factor authentication"""
    
    def __init__(self):
        self.issuer_name = os.getenv("MFA_ISSUER_NAME", "Tourist App")
    
    def generate_totp_secret(self) -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()
    
    def generate_totp_qr_code(self, user_email: str, secret: str, device_name: str) -> str:
        """Generate QR code for TOTP setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        img_base64 = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{img_base64}"
    
    def verify_totp_code(self, secret: str, code: str, window: int = 1) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    
    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for account recovery"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    def verify_backup_code(self, user: User, code: str) -> bool:
        """Verify and consume a backup code"""
        if not user.backup_codes:
            return False
        
        try:
            codes = json.loads(user.backup_codes)
            if code.upper() in codes:
                codes.remove(code.upper())
                user.backup_codes = json.dumps(codes)
                return True
        except (json.JSONDecodeError, AttributeError):
            pass
        
        return False
    
    async def setup_totp(
        self,
        user: User,
        device_name: str,
        db: Session
    ) -> Dict[str, Any]:
        """Setup TOTP for a user"""
        if user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is already enabled for this user"
            )
        
        secret = self.generate_totp_secret()
        qr_code = self.generate_totp_qr_code(user.email, secret, device_name)
        
        # Create MFA device record
        mfa_device = MFADevice(
            user_id=user.id,
            method=MFAMethod.TOTP,
            device_name=device_name,
            secret=secret,
            is_verified=False,
            is_active=True
        )
        db.add(mfa_device)
        
        # Store secret temporarily (user needs to verify before enabling)
        user.mfa_secret = secret
        db.commit()
        
        return {
            "success": True,
            "secret": secret,
            "qr_code": qr_code,
            "manual_entry_key": secret,
            "message": "Scan QR code with authenticator app, then verify with a code"
        }
    
    async def verify_and_enable_totp(
        self,
        user: User,
        code: str,
        db: Session
    ) -> Dict[str, Any]:
        """Verify TOTP code and enable MFA"""
        if not user.mfa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pending TOTP setup found"
            )
        
        if not self.verify_totp_code(user.mfa_secret, code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code"
            )
        
        # Enable MFA
        user.mfa_enabled = True
        user.mfa_secret = user.mfa_secret  # Keep the secret
        
        # Generate backup codes
        backup_codes = self.generate_backup_codes()
        user.backup_codes = json.dumps(backup_codes)
        
        # Mark device as verified
        mfa_device = db.query(MFADevice).filter(
            MFADevice.user_id == user.id,
            MFADevice.method == MFAMethod.TOTP,
            MFADevice.is_verified == False
        ).first()
        
        if mfa_device:
            mfa_device.is_verified = True
        
        db.commit()
        
        return {
            "success": True,
            "message": "MFA enabled successfully",
            "backup_codes": backup_codes,
            "warning": "Save these backup codes in a safe place. They won't be shown again."
        }
    
    async def verify_mfa(
        self,
        user: User,
        code: str,
        method: Optional[str] = None
    ) -> bool:
        """Verify MFA code (TOTP or backup code)"""
        if not user.mfa_enabled:
            return True  # MFA not enabled, skip verification
        
        # Try TOTP first
        if user.mfa_secret and self.verify_totp_code(user.mfa_secret, code):
            return True
        
        # Try backup codes
        if self.verify_backup_code(user, code):
            return True
        
        return False
    
    async def disable_mfa(
        self,
        user: User,
        password: str,
        db: Session
    ) -> Dict[str, Any]:
        """Disable MFA for a user (requires password verification)"""
        from auth import verify_password
        
        if not user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled"
            )
        
        # Verify password
        if not user.hashed_password or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        # Disable MFA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.backup_codes = None
        
        # Deactivate all MFA devices
        db.query(MFADevice).filter(
            MFADevice.user_id == user.id
        ).update({"is_active": False})
        
        db.commit()
        
        return {
            "success": True,
            "message": "MFA disabled successfully"
        }
    
    async def regenerate_backup_codes(
        self,
        user: User,
        db: Session
    ) -> Dict[str, Any]:
        """Regenerate backup codes for a user"""
        if not user.mfa_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="MFA is not enabled"
            )
        
        backup_codes = self.generate_backup_codes()
        user.backup_codes = json.dumps(backup_codes)
        db.commit()
        
        return {
            "success": True,
            "backup_codes": backup_codes,
            "warning": "Save these backup codes in a safe place. They won't be shown again."
        }
    
    async def get_mfa_devices(
        self,
        user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get all MFA devices for a user"""
        devices = db.query(MFADevice).filter(
            MFADevice.user_id == user.id,
            MFADevice.is_active == True
        ).all()
        
        return [
            {
                "id": device.id,
                "method": device.method.value,
                "device_name": device.device_name,
                "is_verified": device.is_verified,
                "last_used": device.last_used.isoformat() if device.last_used else None,
                "created_at": device.created_at.isoformat()
            }
            for device in devices
        ]

