from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Query
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from database import SessionLocal, engine, Base
from models import Tour, Booking, Payment, User, Invoice, Feedback, DataConsent, DataRetentionLog, BackupRecord
from schemas import (
    TourSchema, BookingSchema, PaymentSchema, PaymentRequest,
    PaymentIntentRequest, PaymentIntentResponse, CryptoPaymentRequest,
    PaymentAddressRequest, PaymentAddressResponse, RefundRequest,
    TourCreateSchema, TourUpdateSchema, BookingUpdateSchema, ContactFormSchema,
    UserRegisterSchema, UserLoginSchema, UserSchema, TokenResponse,
    OAuthTokenRequest, OAuthCallbackRequest,
    AccountSettingsUpdateSchema, PasswordUpdateSchema, InvoiceSchema,
    UsageAnalyticsSchema, FeedbackSchema, FeedbackCreateSchema,
    DataExportRequest, DataDeletionRequest, ConsentUpdateRequest,
    RetentionPolicyRequest, RetentionApplyRequest, BackupRequest, RestoreRequest,
    MFASetupRequest, MFAVerifyRequest, MFADisableRequest, BackupCodeVerifyRequest,
    RefreshTokenRequest, SessionRevokeRequest,
    InvitationCreateRequest, InvitationAcceptRequest,
    SAMLInitiateRequest, OIDCInitiateRequest,
    PermissionGrantRequest, PermissionRevokeRequest, PermissionCreateRequest
)
from services.payment_service import PaymentService
from services.solana_service import SolanaService
from services.crypto_service import CryptoService
from services.auth_service import AuthService
from services.compliance_service import ComplianceService
from services.retention_service import RetentionService, RetentionPolicy
from services.encryption_service import get_encryption_service
from services.mfa_service import MFAService
from services.session_service import SessionService
from services.invitation_service import InvitationService
from services.saml_service import SAMLService
from services.oidc_service import OIDCService
from services.rbac_service import RBACService
from auth import get_current_user, get_current_active_user, get_current_admin_user, get_optional_user
from models import User, UserRole

load_dotenv()

# Database tables are created via Alembic migrations
# Run: alembic upgrade head
# Or use: python db_cli.py init

app = FastAPI(title="Tourist App API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Tourist App API", "version": "1.0.0"}

# ========== AUTHENTICATION ENDPOINTS ==========

@app.post("/auth/register", response_model=TokenResponse)
async def register(
    user_data: UserRegisterSchema,
    db: Session = Depends(get_db)
):
    """Register a new user with email/password"""
    auth_service = AuthService()
    result = await auth_service.register_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        username=user_data.username,
        db=db
    )
    return result

@app.post("/auth/login")
async def login(
    credentials: UserLoginSchema,
    request: Request,
    db: Session = Depends(get_db)
):
    """Login with email/password (with session management and MFA support)"""
    auth_service = AuthService()
    user_result = await auth_service.login_user(
        email=credentials.email,
        password=credentials.password,
        db=db
    )
    
    # Get user from database
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Check if MFA is enabled
    if user and user.mfa_enabled:
        # Return partial success - MFA verification required
        return {
            "success": True,
            "mfa_required": True,
            "message": "MFA verification required",
            "user_id": user.id
        }
    
    # Create session
    session_service = SessionService()
    device_info = request.headers.get("User-Agent", "Unknown")
    ip_address = request.client.host if request.client else None
    
    session_result = await session_service.create_session(
        user=user,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent"),
        db=db
    )
    
    return {
        "success": True,
        "access_token": session_result["access_token"],
        "refresh_token": session_result["refresh_token"],
        "token_type": "bearer",
        "user": user_result["user"],
        "expires_at": session_result["expires_at"]
    }

@app.post("/auth/login/mfa-verify")
async def login_mfa_verify(
    request_data: MFAVerifyRequest,
    user_id: int = Query(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Verify MFA code after initial login"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    mfa_service = MFAService()
    is_valid = await mfa_service.verify_mfa(user, request_data.code)
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    
    # Create session after MFA verification
    session_service = SessionService()
    device_info = request.headers.get("User-Agent", "Unknown") if request else "Unknown"
    ip_address = request.client.host if request and request.client else None
    
    session_result = await session_service.create_session(
        user=user,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent") if request else None,
        db=db
    )
    
    return {
        "success": True,
        "access_token": session_result["access_token"],
        "refresh_token": session_result["refresh_token"],
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "avatar_url": user.avatar_url
        },
        "expires_at": session_result["expires_at"]
    }

@app.post("/auth/oauth/token", response_model=TokenResponse)
async def oauth_token_verify(
    oauth_request: OAuthTokenRequest,
    db: Session = Depends(get_db)
):
    """Verify OAuth token from provider (Google, GitHub, etc.)"""
    auth_service = AuthService()
    
    provider = oauth_request.provider.lower()
    if provider == "google":
        result = await auth_service.verify_google_token(oauth_request.token, db)
    elif provider == "github":
        result = await auth_service.verify_github_token(oauth_request.token, db)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported OAuth provider: {provider}"
        )
    
    return result

@app.get("/auth/oauth/{provider}/url")
async def get_oauth_url(provider: str):
    """Get OAuth authorization URL for a provider"""
    auth_service = AuthService()
    return auth_service.get_oauth_url(provider)

@app.get("/auth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback and redirect to frontend with token"""
    from fastapi.responses import RedirectResponse
    
    auth_service = AuthService()
    result = await auth_service.handle_oauth_callback(provider, code, db)
    
    # Redirect to frontend with token
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = f"{frontend_url}/auth/callback?token={result['access_token']}&success=true"
    return RedirectResponse(url=redirect_url)

@app.get("/auth/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "avatar_url": current_user.avatar_url,
        "is_verified": current_user.is_verified,
        "auth_provider": current_user.auth_provider.value
    }

@app.post("/auth/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token"""
    from auth import create_access_token
    access_token = create_access_token(data={"sub": current_user.id, "email": current_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# ========== MFA ENDPOINTS ==========

@app.post("/auth/mfa/setup")
async def setup_mfa(
    request: MFASetupRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Setup MFA (TOTP) for user"""
    mfa_service = MFAService()
    result = await mfa_service.setup_totp(current_user, request.device_name, db)
    return result

@app.post("/auth/mfa/verify-enable")
async def verify_and_enable_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify TOTP code and enable MFA"""
    mfa_service = MFAService()
    result = await mfa_service.verify_and_enable_totp(current_user, request.code, db)
    return result

@app.post("/auth/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verify MFA code during login"""
    mfa_service = MFAService()
    is_valid = await mfa_service.verify_mfa(current_user, request.code)
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid MFA code")
    return {"success": True, "message": "MFA verified"}

@app.post("/auth/mfa/disable")
async def disable_mfa(
    request: MFADisableRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disable MFA for user"""
    mfa_service = MFAService()
    result = await mfa_service.disable_mfa(current_user, request.password, db)
    return result

@app.post("/auth/mfa/regenerate-backup-codes")
async def regenerate_backup_codes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Regenerate backup codes"""
    mfa_service = MFAService()
    result = await mfa_service.regenerate_backup_codes(current_user, db)
    return result

@app.get("/auth/mfa/devices")
async def get_mfa_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all MFA devices for user"""
    mfa_service = MFAService()
    devices = await mfa_service.get_mfa_devices(current_user, db)
    return {"success": True, "devices": devices}

# ========== SESSION MANAGEMENT ENDPOINTS ==========

@app.post("/auth/sessions/refresh")
async def refresh_session_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    session_service = SessionService()
    result = await session_service.refresh_session(request.refresh_token, db)
    return result

@app.get("/auth/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all sessions for current user"""
    session_service = SessionService()
    sessions = await session_service.get_user_sessions(current_user, db)
    return {"success": True, "sessions": sessions}

@app.post("/auth/sessions/revoke")
async def revoke_session(
    request: SessionRevokeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke a session"""
    session_service = SessionService()
    result = await session_service.revoke_session(
        session_id=request.session_id,
        session_token=request.session_token,
        user=current_user,
        db=db
    )
    return result

@app.post("/auth/sessions/revoke-all")
async def revoke_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke all sessions for current user"""
    session_service = SessionService()
    result = await session_service.revoke_all_sessions(current_user, db)
    return result

# ========== INVITATION ENDPOINTS ==========

@app.post("/auth/invitations")
async def create_invitation(
    request: InvitationCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new user invitation (Admin only)"""
    invitation_service = InvitationService()
    role = UserRole[request.role.upper()] if request.role else UserRole.USER
    result = await invitation_service.create_invitation(
        email=request.email,
        invited_by=current_user,
        role=role,
        metadata=request.metadata,
        db=db
    )
    return result

@app.get("/auth/invitations")
async def list_invitations(
    current_user: User = Depends(get_current_active_user),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List invitations"""
    from models import InvitationStatus
    invitation_service = InvitationService()
    status_filter = InvitationStatus[status.upper()] if status else None
    invitations = await invitation_service.list_invitations(
        user=current_user,
        status_filter=status_filter,
        db=db
    )
    return {"success": True, "invitations": invitations}

@app.post("/auth/invitations/accept")
async def accept_invitation(
    request: InvitationAcceptRequest,
    db: Session = Depends(get_db)
):
    """Accept an invitation and create account"""
    invitation_service = InvitationService()
    result = await invitation_service.accept_invitation(
        token=request.token,
        password=request.password,
        full_name=request.full_name,
        username=request.username,
        db=db
    )
    return result

@app.post("/auth/invitations/{invitation_id}/cancel")
async def cancel_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel an invitation"""
    invitation_service = InvitationService()
    result = await invitation_service.cancel_invitation(invitation_id, current_user, db)
    return result

@app.post("/auth/invitations/{invitation_id}/resend")
async def resend_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Resend an invitation"""
    invitation_service = InvitationService()
    result = await invitation_service.resend_invitation(invitation_id, current_user, db)
    return result

# ========== SAML/OIDC ENDPOINTS ==========

@app.post("/auth/saml/initiate")
async def initiate_saml_sso(
    request: SAMLInitiateRequest,
    db: Session = Depends(get_db)
):
    """Initiate SAML SSO"""
    saml_service = SAMLService()
    result = await saml_service.initiate_sso(request.provider_id, db)
    return result

@app.get("/auth/saml/metadata/{provider_id}")
async def get_saml_metadata(
    provider_id: int,
    db: Session = Depends(get_db)
):
    """Get SAML metadata"""
    saml_service = SAMLService()
    metadata = await saml_service.get_metadata(provider_id, db)
    return Response(content=metadata, media_type="application/xml")

@app.post("/auth/oidc/initiate")
async def initiate_oidc_sso(
    request: OIDCInitiateRequest,
    db: Session = Depends(get_db)
):
    """Initiate OIDC SSO"""
    oidc_service = OIDCService()
    result = await oidc_service.get_authorization_url(
        request.provider_id,
        db,
        state=request.state
    )
    return result

@app.get("/auth/oidc/{provider_id}/callback")
async def oidc_callback(
    provider_id: int,
    code: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Handle OIDC callback"""
    from fastapi.responses import RedirectResponse
    
    oidc_service = OIDCService()
    result = await oidc_service.handle_callback(provider_id, code, state, db)
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = f"{frontend_url}/auth/callback?token={result['access_token']}&success=true"
    return RedirectResponse(url=redirect_url)

# ========== RBAC ENDPOINTS ==========

@app.get("/auth/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for current user"""
    rbac_service = RBACService()
    permissions = await rbac_service.get_user_permissions(current_user, db)
    return {"success": True, "permissions": permissions}

@app.post("/auth/permissions/grant")
async def grant_permission(
    request: PermissionGrantRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Grant permission to user (Admin only)"""
    rbac_service = RBACService()
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await rbac_service.grant_permission(user, request.permission, db)
    return result

@app.post("/auth/permissions/revoke")
async def revoke_permission(
    request: PermissionRevokeRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Revoke permission from user (Admin only)"""
    rbac_service = RBACService()
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await rbac_service.revoke_permission(user, request.permission, db)
    return result

@app.post("/auth/permissions/create")
async def create_permission(
    request: PermissionCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new permission (Admin only)"""
    rbac_service = RBACService()
    result = await rbac_service.create_permission(
        request.name,
        request.resource,
        request.action,
        request.description,
        db
    )
    return result

@app.post("/auth/permissions/initialize")
async def initialize_permissions(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Initialize default permissions (Admin only)"""
    rbac_service = RBACService()
    result = await rbac_service.initialize_default_permissions(db)
    return result

@app.get("/tours", response_model=List[TourSchema])
async def get_tours(db: Session = Depends(get_db)):
    tours = db.query(Tour).all()
    return tours

@app.get("/tours/{tour_id}", response_model=TourSchema)
async def get_tour(tour_id: int, db: Session = Depends(get_db)):
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour

@app.post("/tours", response_model=TourSchema)
async def create_tour(
    tour: TourCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Create a new tour (Admin only)"""
    db_tour = Tour(**tour.dict())
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour

@app.put("/tours/{tour_id}", response_model=TourSchema)
async def update_tour(
    tour_id: int,
    tour: TourUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a tour (Admin only)"""
    db_tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    update_data = tour.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tour, field, value)
    
    db.commit()
    db.refresh(db_tour)
    return db_tour

@app.delete("/tours/{tour_id}")
async def delete_tour(
    tour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a tour (Admin only)"""
    db_tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    db.delete(db_tour)
    db.commit()
    return {"message": "Tour deleted successfully"}

@app.get("/bookings", response_model=List[BookingSchema])
async def get_bookings(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
    user_only: bool = Query(False, description="Get only current user's bookings")
):
    """Get all bookings with tour and payment information"""
    if user_only and current_user:
        bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()
    else:
        bookings = db.query(Booking).all()
    result = []
    for booking in bookings:
        booking_dict = {
            "id": booking.id,
            "tour_id": booking.tour_id,
            "user_email": booking.user_email,
            "booking_date": booking.booking_date,
            "status": booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
            "notes": booking.notes,
        }
        # Include tour information
        if booking.tour:
            booking_dict["tour_name"] = booking.tour.name
        # Include payment information
        if booking.payments:
            latest_payment = booking.payments[-1]  # Get the most recent payment
            booking_dict["payment_method"] = latest_payment.payment_method.value if hasattr(latest_payment.payment_method, 'value') else str(latest_payment.payment_method)
            booking_dict["amount"] = latest_payment.amount
        result.append(booking_dict)
    return result

@app.post("/bookings", response_model=BookingSchema)
async def create_booking(
    booking: BookingSchema,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Create a new booking"""
    booking_data = booking.dict()
    # Link booking to authenticated user if available
    if current_user:
        booking_data["user_id"] = current_user.id
        if not booking_data.get("user_email"):
            booking_data["user_email"] = current_user.email
    
    db_booking = Booking(**booking_data)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@app.get("/bookings/{booking_id}", response_model=BookingSchema)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Get a specific booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@app.patch("/bookings/{booking_id}", response_model=BookingSchema)
async def update_booking(
    booking_id: int,
    booking: BookingUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update a booking status (Admin only)"""
    db_booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not db_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    update_data = booking.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_booking, field, value)
    
    db.commit()
    db.refresh(db_booking)
    return db_booking

# ========== DEBIT CARD PAYMENT ENDPOINTS (STRIPE) ==========

@app.post("/payments/stripe/intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    intent_request: PaymentIntentRequest,
    db: Session = Depends(get_db)
):
    """Create a payment intent for debit/credit card payments"""
    try:
        payment_service = PaymentService()
        result = await payment_service.create_payment_intent(
            amount=intent_request.amount,
            currency=intent_request.currency,
            metadata={
                "tour_id": str(intent_request.tour_id),
                "user_email": intent_request.user_email or ""
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/stripe")
async def process_stripe_payment(
    payment_request: PaymentRequest,
    db: Session = Depends(get_db)
):
    """Process a Stripe payment with debit/credit card"""
    try:
        payment_service = PaymentService()
        result = await payment_service.process_stripe_payment(
            payment_method_id=payment_request.payment_method_id,
            amount=payment_request.amount,
            tour_id=payment_request.tour_id,
            user_email=payment_request.user_email,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Payment failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/stripe/confirm")
async def confirm_stripe_payment(
    payment_intent_id: str,
    tour_id: int,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Confirm a Stripe payment intent"""
    try:
        payment_service = PaymentService()
        result = await payment_service.confirm_payment_intent(
            payment_intent_id=payment_intent_id,
            tour_id=tour_id,
            user_email=user_email,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Payment confirmation failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        payment_service = PaymentService()
        result = payment_service.handle_webhook(payload, stripe_signature or "")
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/stripe/refund")
async def refund_stripe_payment(
    refund_request: RefundRequest,
    db: Session = Depends(get_db)
):
    """Refund a Stripe payment"""
    try:
        payment_service = PaymentService()
        result = await payment_service.refund_payment(
            payment_id=refund_request.payment_id,
            amount=refund_request.amount,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Refund failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== CRYPTO PAYMENT ENDPOINTS ==========

@app.get("/payments/address/{currency}", response_model=PaymentAddressResponse)
async def get_payment_address(currency: str):
    """Get payment address for a specific cryptocurrency"""
    try:
        currency_lower = currency.lower()
        
        if currency_lower == "solana" or currency_lower == "sol":
            solana_service = SolanaService()
            result = solana_service.get_payment_address()
        elif currency_lower == "bitcoin" or currency_lower == "btc":
            crypto_service = CryptoService()
            result = await crypto_service.get_bitcoin_payment_address()
        elif currency_lower == "ethereum" or currency_lower == "eth":
            crypto_service = CryptoService()
            result = await crypto_service.get_ethereum_payment_address()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported currency: {currency}")
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get payment address"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/solana")
async def process_solana_payment(
    payment_request: CryptoPaymentRequest,
    db: Session = Depends(get_db)
):
    """Process a Solana payment"""
    try:
        solana_service = SolanaService()
        result = await solana_service.verify_solana_payment(
            signature=payment_request.transaction_hash,
            amount=payment_request.amount,
            public_key=payment_request.public_key or "",
            tour_id=payment_request.tour_id,
            user_email=payment_request.user_email,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Payment verification failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payments/solana/status/{signature}")
async def check_solana_payment_status(signature: str):
    """Check the status of a Solana payment"""
    try:
        solana_service = SolanaService()
        result = await solana_service.check_payment_status(signature)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/bitcoin")
async def process_bitcoin_payment(
    payment_request: CryptoPaymentRequest,
    db: Session = Depends(get_db)
):
    """Process a Bitcoin payment"""
    try:
        crypto_service = CryptoService()
        result = await crypto_service.verify_bitcoin_payment(
            tx_hash=payment_request.transaction_hash,
            amount=payment_request.amount,
            tour_id=payment_request.tour_id,
            user_email=payment_request.user_email,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Payment verification failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/ethereum")
async def process_ethereum_payment(
    payment_request: CryptoPaymentRequest,
    db: Session = Depends(get_db)
):
    """Process an Ethereum payment"""
    try:
        crypto_service = CryptoService()
        result = await crypto_service.verify_ethereum_payment(
            tx_hash=payment_request.transaction_hash,
            amount=payment_request.amount,
            tour_id=payment_request.tour_id,
            user_email=payment_request.user_email,
            db=db
        )
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Payment verification failed"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payments/crypto/status/{currency}/{tx_hash}")
async def check_crypto_payment_status(currency: str, tx_hash: str):
    """Check the status of a cryptocurrency payment"""
    try:
        crypto_service = CryptoService()
        result = await crypto_service.check_crypto_payment_status(tx_hash, currency)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========== PAYMENT HISTORY ==========

@app.get("/payments", response_model=List[PaymentSchema])
async def get_payments(db: Session = Depends(get_db)):
    """Get all payment records"""
    payments = db.query(Payment).all()
    return payments

@app.get("/payments/{payment_id}", response_model=PaymentSchema)
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a specific payment record"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    from database import check_database_connection
    db_healthy = check_database_connection()
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected"
    }

@app.get("/health/database")
async def database_health_check():
    """Comprehensive database health check"""
    from db_utils import health_check_db
    return health_check_db()

@app.get("/database/info")
async def get_database_info_endpoint():
    """Get database connection information"""
    from database import get_database_info
    return get_database_info()

@app.get("/database/stats")
async def get_database_stats():
    """Get database statistics"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.get_table_stats()

@app.get("/database/pool-stats")
async def get_pool_stats():
    """Get connection pool statistics"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.get_connection_pool_stats()

@app.post("/database/backup")
async def create_backup(
    backup_name: Optional[str] = None,
    encrypt: bool = True,
    current_user: User = Depends(get_current_admin_user)
):
    """Create a database backup (with encryption) - Admin only"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.backup_database(backup_name=backup_name, encrypt=encrypt)

@app.get("/database/backups")
async def list_backups():
    """List all available backups"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.list_backups()

# ========== CUSTOMER DASHBOARD ENDPOINTS ==========

@app.get("/dashboard/account", response_model=dict)
async def get_account_settings(
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get account settings for a user"""
    if not user_email:
        # In a real app, get from authenticated user
        return {"error": "User email required"}
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return {
            "email": user_email,
            "full_name": None,
            "username": None,
            "phone_number": None,
            "avatar_url": None,
            "is_verified": False
        }
    
    return {
        "email": user.email,
        "full_name": user.full_name,
        "username": user.username,
        "phone_number": user.phone_number,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }

@app.patch("/dashboard/account")
async def update_account_settings(
    settings: AccountSettingsUpdateSchema,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Update account settings"""
    if not user_email:
        raise HTTPException(status_code=400, detail="User email required")
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = settings.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return {"success": True, "message": "Account settings updated successfully"}

@app.get("/dashboard/invoices", response_model=List[InvoiceSchema])
async def get_user_invoices(
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get invoices for a user"""
    if not user_email:
        return []
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return []
    
    invoices = db.query(Invoice).filter(Invoice.user_id == user.id).order_by(Invoice.created_at.desc()).all()
    return invoices

@app.get("/dashboard/invoices/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a specific invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@app.get("/dashboard/analytics", response_model=UsageAnalyticsSchema)
async def get_usage_analytics(
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get usage analytics for a user"""
    if not user_email:
        return {
            "total_bookings": 0,
            "total_spent": 0.0,
            "favorite_destinations": [],
            "booking_trends": {},
            "payment_methods_used": {},
            "recent_activity": []
        }
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return {
            "total_bookings": 0,
            "total_spent": 0.0,
            "favorite_destinations": [],
            "booking_trends": {},
            "payment_methods_used": {},
            "recent_activity": []
        }
    
    # Get bookings
    bookings = db.query(Booking).filter(Booking.user_email == user_email).all()
    total_bookings = len(bookings)
    
    # Get payments and calculate total spent
    payments = db.query(Payment).join(Booking).filter(Booking.user_email == user_email).filter(Payment.status == "completed").all()
    total_spent = sum(p.amount for p in payments)
    
    # Get favorite destinations
    tour_ids = [b.tour_id for b in bookings]
    tours = db.query(Tour).filter(Tour.id.in_(tour_ids)).all() if tour_ids else []
    location_counts = {}
    for booking in bookings:
        tour = next((t for t in tours if t.id == booking.tour_id), None)
        if tour and tour.location:
            location_counts[tour.location] = location_counts.get(tour.location, 0) + 1
    favorite_destinations = sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Booking trends (last 6 months)
    from datetime import datetime, timedelta
    from collections import defaultdict
    trends = defaultdict(int)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    for booking in bookings:
        if booking.created_at and booking.created_at >= six_months_ago:
            month_key = booking.created_at.strftime("%Y-%m")
            trends[month_key] += 1
    
    # Payment methods used
    payment_methods = defaultdict(int)
    for payment in payments:
        method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
        payment_methods[method] += 1
    
    # Recent activity
    recent_activity = []
    for booking in bookings[:10]:
        tour = next((t for t in tours if t.id == booking.tour_id), None)
        recent_activity.append({
            "type": "booking",
            "description": f"Booked {tour.name if tour else 'Tour'}" if tour else "Made a booking",
            "date": booking.created_at.isoformat() if booking.created_at else None
        })
    
    return {
        "total_bookings": total_bookings,
        "total_spent": total_spent,
        "favorite_destinations": [{"location": loc, "count": count} for loc, count in favorite_destinations],
        "booking_trends": dict(trends),
        "payment_methods_used": dict(payment_methods),
        "recent_activity": recent_activity
    }

@app.get("/dashboard/documentation")
async def get_documentation_links():
    """Get documentation links"""
    return {
        "links": [
            {
                "title": "Getting Started Guide",
                "url": "/docs/getting-started",
                "description": "Learn how to book your first tour"
            },
            {
                "title": "Payment Methods",
                "url": "/docs/payments",
                "description": "Information about payment options"
            },
            {
                "title": "API Documentation",
                "url": "/docs/api",
                "description": "Complete API reference"
            },
            {
                "title": "FAQ",
                "url": "/support",
                "description": "Frequently asked questions"
            }
        ]
    }

@app.post("/dashboard/feedback", response_model=FeedbackSchema)
async def submit_feedback(
    feedback: FeedbackCreateSchema,
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback"""
    user = None
    if user_email:
        user = db.query(User).filter(User.email == user_email).first()
    
    db_feedback = Feedback(
        user_id=user.id if user else None,
        user_email=user_email or "anonymous@example.com",
        feedback_type=feedback.feedback_type,
        subject=feedback.subject,
        message=feedback.message,
        rating=feedback.rating,
        status="open"
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@app.get("/dashboard/feedback", response_model=List[FeedbackSchema])
async def get_user_feedback(
    user_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get feedback submitted by user"""
    if not user_email:
        return []
    
    feedbacks = db.query(Feedback).filter(Feedback.user_email == user_email).order_by(Feedback.created_at.desc()).all()
    return feedbacks

# ========== SUPPORT ENDPOINTS ==========

@app.post("/support/contact")
async def submit_contact_form(contact: ContactFormSchema, db: Session = Depends(get_db)):
    """Submit a contact form"""
    # In a real application, you would save this to a database or send an email
    # For now, we'll just return a success message
    return {
        "success": True,
        "message": "Thank you for contacting us! We'll get back to you soon.",
        "data": {
            "name": contact.name,
            "email": contact.email,
            "subject": contact.subject
        }
    }

# ========== SECURITY & COMPLIANCE ENDPOINTS ==========

@app.post("/security/data/export")
async def export_user_data(
    request: DataExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export user data (GDPR Right to Access)"""
    # Users can only export their own data, admins can export any user's data
    user_id = request.user_id
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only export your own data")
    
    compliance_service = ComplianceService()
    result = compliance_service.export_user_data(user_id, db)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Export failed"))
    
    if request.format == "csv":
        csv_data = compliance_service.export_data_csv(user_id, db)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=user_data_{user_id}.csv"}
        )
    else:
        json_data = compliance_service.export_data_json(user_id, db)
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=user_data_{user_id}.json"}
        )

@app.post("/security/data/delete")
async def delete_user_data(
    request: DataDeletionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete or anonymize user data (GDPR Right to be Forgotten) - Admin only"""
    compliance_service = ComplianceService()
    result = compliance_service.delete_user_data(
        request.user_id,
        db,
        anonymize=request.anonymize
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Deletion failed"))
    
    return result

@app.get("/security/data/consent/{user_id}")
async def get_consent_status(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user consent status"""
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own consent status")
    
    compliance_service = ComplianceService()
    return compliance_service.get_consent_status(user_id, db)

@app.post("/security/data/consent/{user_id}")
async def update_consent(
    user_id: int,
    request: ConsentUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user consent"""
    if current_user.role.value != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your own consent")
    
    compliance_service = ComplianceService()
    return compliance_service.update_consent(user_id, request.consent_type, request.granted, db)

@app.post("/security/retention/policy")
async def create_retention_policy(
    request: RetentionPolicyRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Create or update a retention policy - Admin only"""
    retention_service = RetentionService()
    policy = RetentionPolicy(
        data_type=request.data_type,
        retention_days=request.retention_days,
        action=request.action or "anonymize"
    )
    retention_service.add_policy(policy)
    return {
        "success": True,
        "message": f"Retention policy for {request.data_type} created",
        "policy": {
            "data_type": policy.data_type,
            "retention_days": policy.retention_days,
            "action": policy.action
        }
    }

@app.post("/security/retention/apply")
async def apply_retention_policy(
    request: RetentionApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Apply retention policies - Admin only"""
    retention_service = RetentionService()
    
    if request.data_type:
        result = retention_service.apply_retention_policy(
            request.data_type,
            db,
            dry_run=request.dry_run
        )
    else:
        result = retention_service.apply_all_policies(db, dry_run=request.dry_run)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Retention policy application failed"))
    
    return result

@app.get("/security/retention/policies")
async def list_retention_policies(
    current_user: User = Depends(get_current_admin_user)
):
    """List all retention policies - Admin only"""
    retention_service = RetentionService()
    policies = {}
    for data_type, policy in retention_service.policies.items():
        policies[data_type] = {
            "retention_days": policy.retention_days,
            "action": policy.action,
            "cutoff_date": policy.get_cutoff_date().isoformat()
        }
    return {
        "success": True,
        "policies": policies
    }

@app.post("/security/backup/create")
async def create_encrypted_backup(
    request: BackupRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Create an encrypted database backup - Admin only"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    result = manager.backup_database(
        backup_name=request.backup_name,
        encrypt=request.encrypt
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Backup failed"))
    
    return result

@app.post("/security/backup/restore")
async def restore_backup(
    request: RestoreRequest,
    current_user: User = Depends(get_current_admin_user)
):
    """Restore database from backup - Admin only"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    result = manager.restore_database(
        backup_path=request.backup_path,
        drop_existing=request.drop_existing,
        encrypted=request.encrypted
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Restore failed"))
    
    return result

@app.get("/security/backup/list")
async def list_backups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all backups - Admin only"""
    from db_utils import DatabaseManager
    from models import BackupRecord
    manager = DatabaseManager()
    
    # Get backups from filesystem
    file_backups = manager.list_backups()
    
    # Get backups from database
    db_backups = db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()
    db_backup_list = [
        {
            "name": b.backup_name,
            "path": b.backup_path,
            "size": b.file_size,
            "size_mb": round(b.file_size / (1024 * 1024), 2),
            "encrypted": b.encrypted,
            "status": b.status,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        for b in db_backups
    ]
    
    return {
        "success": True,
        "file_backups": file_backups,
        "database_backups": db_backup_list
    }

@app.get("/security/encryption/key/generate")
async def generate_encryption_key(
    current_user: User = Depends(get_current_admin_user)
):
    """Generate a new encryption key (for setup) - Admin only"""
    encryption_service = get_encryption_service()
    key = encryption_service.generate_encryption_key()
    return {
        "success": True,
        "encryption_key": key,
        "message": "Add this key to your .env file as ENCRYPTION_KEY",
        "warning": "Keep this key secure and never commit it to version control!"
    }

# Initialize scheduler service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    from services.scheduler_service import get_scheduler_service
    scheduler = get_scheduler_service()
    scheduler.start()
    logger.info("Application startup: Scheduler service initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    from services.scheduler_service import get_scheduler_service
    scheduler = get_scheduler_service()
    scheduler.stop()
    logger.info("Application shutdown: Scheduler service stopped")

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)

