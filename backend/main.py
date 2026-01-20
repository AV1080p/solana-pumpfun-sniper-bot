from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from fastapi import Query
import os
import logging
import json
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from database import SessionLocal, engine, Base
from models import (
    Tour, Booking, Payment, User, Invoice, Feedback, DataConsent, DataRetentionLog, BackupRecord, AuditLog,
    ForumPost, ForumReply, SupportTicket, SupportMessage, FAQ, SupportAgent, Tutorial, LocalSupport,
    AISupportConversation, AISupportMessage
)
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
    PermissionGrantRequest, PermissionRevokeRequest, PermissionCreateRequest,
    AdminAnalyticsResponse, UserUpdateRequest, UserListResponse,
    BillingSummaryResponse, UsageReportRequest, SystemHealthResponse,
    AuditLogResponse, AuditLogFilterRequest,
    ChatRoomSchema, MessageSchema, MessageCreateRequest, ChatRoomCreateRequest,
    AIConversationSchema, AIMessageSchema, AIChatRequest,
    CallSessionSchema, CallInitiateRequest,
    BroadcastAlertSchema, BroadcastCreateRequest,
    ForumCategorySchema, ForumPostSchema, ForumPostCreateRequest,
    ForumReplySchema, ForumReplyCreateRequest, TranslationRequest,
    SupportTicketCreateRequest, SupportTicketSchema, SupportMessageCreateRequest, SupportMessageSchema,
    SupportTicketUpdateRequest, FAQSchema, FAQCreateRequest, FAQUpdateRequest, FAQFeedbackRequest,
    TutorialSchema, TutorialCreateRequest, SupportAgentSchema, LocalSupportSchema,
    AISupportRequest, AISupportResponse, SupportTicketSearchRequest
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
from services.communication_service import CommunicationService
from services.support_service import SupportService
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
    request: Request,
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

# ========== SUPPORT SYSTEM ENDPOINTS ==========

# ========== AI ASSISTANT ==========

@app.post("/support/ai/chat", response_model=AISupportResponse)
async def ai_support_chat(
    request: AISupportRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """AI support assistant with natural language queries and proactive suggestions"""
    support_service = SupportService()
    result = await support_service.process_ai_query(
        message=request.message,
        user_id=current_user.id if current_user else None,
        session_id=request.session_id,
        context=request.context,
        db=db
    )
    return result

@app.get("/support/ai/conversations/{session_id}")
async def get_ai_conversation(
    session_id: str,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get AI support conversation history"""
    conversation = db.query(AISupportConversation).filter(
        AISupportConversation.session_id == session_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check access
    if current_user and conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = db.query(AISupportMessage).filter(
        AISupportMessage.conversation_id == conversation.id
    ).order_by(AISupportMessage.created_at.asc()).all()
    
    return {
        "success": True,
        "conversation": {
            "session_id": conversation.session_id,
            "user_intent": conversation.user_intent,
            "resolved": conversation.resolved,
            "escalated_to_human": conversation.escalated_to_human,
            "created_at": conversation.created_at
        },
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "confidence_score": msg.confidence_score,
                "suggested_faqs": json.loads(msg.suggested_faqs) if msg.suggested_faqs else [],
                "created_at": msg.created_at
            }
            for msg in messages
        ]
    }

# ========== SUPPORT TICKETS ==========

@app.post("/support/tickets", response_model=SupportTicketSchema)
async def create_support_ticket(
    request: SupportTicketCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Create a new support ticket"""
    support_service = SupportService()
    user_email = current_user.email if current_user else None
    
    if not user_email:
        raise HTTPException(status_code=400, detail="User email required")
    
    result = await support_service.create_ticket(
        user_id=current_user.id if current_user else None,
        user_email=user_email,
        subject=request.subject,
        description=request.description,
        category=request.category,
        priority=request.priority or "normal",
        language=request.language or "en",
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result["ticket"]

@app.get("/support/tickets", response_model=List[SupportTicketSchema])
async def get_support_tickets(
    current_user: Optional[User] = Depends(get_optional_user),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get support tickets for current user"""
    support_service = SupportService()
    user_email = current_user.email if current_user else None
    
    if not user_email:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    tickets = await support_service.get_user_tickets(
        user_id=current_user.id if current_user else None,
        user_email=user_email,
        status=status,
        db=db
    )
    
    return tickets

@app.get("/support/tickets/{ticket_id}", response_model=SupportTicketSchema)
async def get_support_ticket(
    ticket_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get a specific support ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    if current_user:
        if ticket.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return ticket

@app.get("/support/tickets/{ticket_id}/messages", response_model=List[SupportMessageSchema])
async def get_ticket_messages(
    ticket_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get messages for a support ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    if current_user:
        if ticket.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    messages = db.query(SupportMessage).filter(
        and_(
            SupportMessage.ticket_id == ticket_id,
            SupportMessage.is_internal == False  # Don't show internal notes to users
        )
    ).order_by(SupportMessage.created_at.asc()).all()
    
    return messages

@app.post("/support/tickets/{ticket_id}/messages", response_model=SupportMessageSchema)
async def add_ticket_message(
    ticket_id: int,
    request: SupportMessageCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a message to a support ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check access
    if ticket.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Access denied")
    
    support_service = SupportService()
    sender_type = "agent" if current_user.role == UserRole.ADMIN else "user"
    
    result = await support_service.add_message_to_ticket(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        sender_email=current_user.email,
        sender_type=sender_type,
        content=request.content,
        is_internal=False,
        attachments=request.attachments,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result["message"]

@app.patch("/support/tickets/{ticket_id}", response_model=SupportTicketSchema)
async def update_support_ticket(
    ticket_id: int,
    request: SupportTicketUpdateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update a support ticket (Admin only)"""
    support_service = SupportService()
    result = await support_service.update_ticket(
        ticket_id=ticket_id,
        status=request.status,
        priority=request.priority,
        assigned_to=request.assigned_to,
        resolution=request.resolution,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result["ticket"]

# ========== FAQ ==========

@app.get("/support/faqs", response_model=List[FAQSchema])
async def get_faqs(
    category: Optional[str] = None,
    language: str = Query("en"),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get FAQs with optional filtering"""
    support_service = SupportService()
    faqs = await support_service.get_faqs(
        category=category,
        language=language,
        search=search,
        db=db
    )
    
    result = []
    for faq in faqs:
        faq_dict = {
            "id": faq.id,
            "category": faq.category,
            "question": faq.question,
            "answer": faq.answer,
            "language": faq.language,
            "order": faq.order,
            "view_count": faq.view_count,
            "helpful_count": faq.helpful_count,
            "not_helpful_count": faq.not_helpful_count,
            "tags": json.loads(faq.tags) if faq.tags else None,
            "created_at": faq.created_at
        }
        result.append(faq_dict)
    
    return result

@app.get("/support/faqs/{faq_id}", response_model=FAQSchema)
async def get_faq(
    faq_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific FAQ"""
    support_service = SupportService()
    faq = await support_service.get_faq(faq_id, db)
    
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    
    return {
        "id": faq.id,
        "category": faq.category,
        "question": faq.question,
        "answer": faq.answer,
        "language": faq.language,
        "order": faq.order,
        "view_count": faq.view_count,
        "helpful_count": faq.helpful_count,
        "not_helpful_count": faq.not_helpful_count,
        "tags": json.loads(faq.tags) if faq.tags else None,
        "created_at": faq.created_at
    }

@app.post("/support/faqs/{faq_id}/feedback")
async def submit_faq_feedback(
    faq_id: int,
    request: FAQFeedbackRequest,
    db: Session = Depends(get_db)
):
    """Submit feedback on FAQ helpfulness"""
    support_service = SupportService()
    result = await support_service.record_faq_feedback(faq_id, request.helpful, db)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result

@app.post("/support/faqs", response_model=FAQSchema)
async def create_faq(
    request: FAQCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new FAQ (Admin only)"""
    faq = FAQ(
        category=request.category,
        question=request.question,
        answer=request.answer,
        language=request.language or "en",
        order=request.order or 0,
        tags=json.dumps(request.tags) if request.tags else None,
        is_published=True
    )
    
    db.add(faq)
    db.commit()
    db.refresh(faq)
    
    return {
        "id": faq.id,
        "category": faq.category,
        "question": faq.question,
        "answer": faq.answer,
        "language": faq.language,
        "order": faq.order,
        "view_count": faq.view_count,
        "helpful_count": faq.helpful_count,
        "not_helpful_count": faq.not_helpful_count,
        "tags": json.loads(faq.tags) if faq.tags else None,
        "created_at": faq.created_at
    }

# ========== TUTORIALS ==========

@app.get("/support/tutorials", response_model=List[TutorialSchema])
async def get_tutorials(
    category: Optional[str] = None,
    language: str = Query("en"),
    db: Session = Depends(get_db)
):
    """Get tutorials with optional filtering"""
    support_service = SupportService()
    tutorials = await support_service.get_tutorials(
        category=category,
        language=language,
        db=db
    )
    
    result = []
    for tutorial in tutorials:
        tutorial_dict = {
            "id": tutorial.id,
            "title": tutorial.title,
            "category": tutorial.category,
            "description": tutorial.description,
            "video_url": tutorial.video_url,
            "thumbnail_url": tutorial.thumbnail_url,
            "duration_seconds": tutorial.duration_seconds,
            "language": tutorial.language,
            "order": tutorial.order,
            "view_count": tutorial.view_count,
            "tags": json.loads(tutorial.tags) if tutorial.tags else None,
            "created_at": tutorial.created_at
        }
        result.append(tutorial_dict)
    
    return result

@app.get("/support/tutorials/{tutorial_id}", response_model=TutorialSchema)
async def get_tutorial(
    tutorial_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific tutorial"""
    support_service = SupportService()
    tutorial = await support_service.get_tutorial(tutorial_id, db)
    
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")
    
    return {
        "id": tutorial.id,
        "title": tutorial.title,
        "description": tutorial.description,
        "category": tutorial.category,
        "video_url": tutorial.video_url,
        "thumbnail_url": tutorial.thumbnail_url,
        "duration_seconds": tutorial.duration_seconds,
        "language": tutorial.language,
        "order": tutorial.order,
        "view_count": tutorial.view_count,
        "tags": json.loads(tutorial.tags) if tutorial.tags else None,
        "created_at": tutorial.created_at
    }

# ========== LOCAL SUPPORT ==========

@app.get("/support/local", response_model=List[LocalSupportSchema])
async def get_local_support(
    country: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get local support locations"""
    support_service = SupportService()
    locations = await support_service.get_local_support(
        country=country,
        city=city,
        db=db
    )
    
    result = []
    for location in locations:
        location_dict = {
            "id": location.id,
            "location": location.location,
            "country": location.country,
            "city": location.city,
            "address": location.address,
            "phone": location.phone,
            "email": location.email,
            "languages": json.loads(location.languages) if location.languages else [],
            "services": json.loads(location.services) if location.services else None,
            "availability_hours": json.loads(location.availability_hours) if location.availability_hours else None,
            "coordinates_lat": location.coordinates_lat,
            "coordinates_lng": location.coordinates_lng
        }
        result.append(location_dict)
    
    return result

# ========== SUPPORT AGENTS ==========

@app.get("/support/agents", response_model=List[SupportAgentSchema])
async def get_available_agents(
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get available support agents"""
    support_service = SupportService()
    agents = await support_service.get_available_agents(
        language=language,
        db=db
    )
    
    result = []
    for agent in agents:
        agent_dict = {
            "id": agent.id,
            "user_id": agent.user_id,
            "languages": json.loads(agent.languages) if agent.languages else [],
            "specialties": json.loads(agent.specialties) if agent.specialties else None,
            "availability_status": agent.availability_status,
            "rating": agent.rating,
            "total_resolved": agent.total_resolved,
            "response_time_avg": agent.response_time_avg
        }
        result.append(agent_dict)
    
    return result

# ========== LEGACY CONTACT FORM ==========

@app.post("/support/contact")
async def submit_contact_form(contact: ContactFormSchema, db: Session = Depends(get_db)):
    """Submit a contact form (creates a support ticket)"""
    support_service = SupportService()
    result = await support_service.create_ticket(
        user_id=None,
        user_email=contact.email,
        subject=contact.subject,
        description=contact.message,
        category="general",
        priority="normal",
        language="en",
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return {
        "success": True,
        "message": "Thank you for contacting us! We'll get back to you soon.",
        "ticket_number": result.get("ticket_number")
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

# ========== ADMIN DASHBOARD ENDPOINTS ==========

def create_audit_log(
    db: Session,
    user_id: Optional[int],
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """Helper function to create audit log entries"""
    import json
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=json.dumps(metadata) if metadata else None
    )
    db.add(audit)
    db.commit()

@app.get("/admin/analytics", response_model=AdminAnalyticsResponse)
async def get_admin_analytics(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get real-time analytics for admin dashboard"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    from sqlalchemy import func, and_
    
    # Total counts
    total_users = db.query(func.count(User.id)).scalar()
    total_bookings = db.query(func.count(Booking.id)).scalar()
    total_payments = db.query(func.count(Payment.id)).scalar()
    
    # Revenue calculations
    completed_payments = db.query(Payment).filter(Payment.status == "completed").all()
    total_revenue = sum(p.amount for p in completed_payments)
    
    # Active users (logged in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users_30d = db.query(func.count(User.id)).filter(
        User.last_login >= thirty_days_ago
    ).scalar()
    
    # New users (last 30 days)
    new_users_30d = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar()
    
    # Revenue by month (last 6 months)
    revenue_by_month = defaultdict(float)
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    recent_payments = db.query(Payment).filter(
        and_(Payment.status == "completed", Payment.created_at >= six_months_ago)
    ).all()
    for payment in recent_payments:
        month_key = payment.created_at.strftime("%Y-%m")
        revenue_by_month[month_key] += payment.amount
    
    # Bookings by status
    bookings_by_status = defaultdict(int)
    for booking in db.query(Booking).all():
        status = booking.status.value if hasattr(booking.status, 'value') else str(booking.status)
        bookings_by_status[status] += 1
    
    # Payments by method
    payments_by_method = defaultdict(float)
    for payment in completed_payments:
        method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
        payments_by_method[method] += payment.amount
    
    # Top tours by bookings
    tour_bookings = db.query(
        Booking.tour_id,
        func.count(Booking.id).label('count')
    ).group_by(Booking.tour_id).order_by(func.count(Booking.id).desc()).limit(5).all()
    
    top_tours = []
    for tour_id, count in tour_bookings:
        tour = db.query(Tour).filter(Tour.id == tour_id).first()
        if tour:
            top_tours.append({
                "id": tour.id,
                "name": tour.name,
                "bookings_count": count
            })
    
    # Recent activity (last 10 bookings)
    recent_bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(10).all()
    recent_activity = []
    for booking in recent_bookings:
        tour = db.query(Tour).filter(Tour.id == booking.tour_id).first()
        recent_activity.append({
            "type": "booking",
            "description": f"New booking for {tour.name if tour else 'Tour'}" if tour else "New booking",
            "date": booking.created_at.isoformat() if booking.created_at else None,
            "user_email": booking.user_email
        })
    
    # Log audit
    create_audit_log(
        db, current_user.id, "admin.analytics.view", "analytics",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "total_revenue": total_revenue,
        "total_payments": total_payments,
        "active_users_30d": active_users_30d,
        "new_users_30d": new_users_30d,
        "revenue_by_month": dict(revenue_by_month),
        "bookings_by_status": dict(bookings_by_status),
        "payments_by_method": dict(payments_by_method),
        "top_tours": top_tours,
        "recent_activity": recent_activity
    }

@app.get("/admin/users", response_model=List[UserListResponse])
async def list_users(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None
):
    """List all users with statistics"""
    from sqlalchemy import or_
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
        )
    
    users = query.offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        # Get user statistics
        bookings_count = db.query(func.count(Booking.id)).filter(Booking.user_id == user.id).scalar()
        payments = db.query(Payment).join(Booking).filter(Booking.user_id == user.id).filter(Payment.status == "completed").all()
        total_spent = sum(p.amount for p in payments)
        
        result.append({
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "total_bookings": bookings_count,
            "total_spent": total_spent
        })
    
    create_audit_log(
        db, current_user.id, "admin.users.list", "user",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return result

@app.get("/admin/users/{user_id}", response_model=UserListResponse)
async def get_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get a specific user with statistics"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bookings_count = db.query(func.count(Booking.id)).filter(Booking.user_id == user.id).scalar()
    payments = db.query(Payment).join(Booking).filter(Booking.user_id == user.id).filter(Payment.status == "completed").all()
    total_spent = sum(p.amount for p in payments)
    
    create_audit_log(
        db, current_user.id, "admin.users.view", "user", user_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "total_bookings": bookings_count,
        "total_spent": total_spent
    }

@app.patch("/admin/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.dict(exclude_unset=True)
    
    # Handle role update
    if "role" in update_data:
        try:
            update_data["role"] = UserRole[update_data["role"].upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid role")
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    create_audit_log(
        db, current_user.id, "admin.users.update", "user", user_id,
        description=f"Updated user {user.email}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
        metadata=update_data
    )
    
    return {"success": True, "message": "User updated successfully", "user": user}

@app.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user (Admin only)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_email = user.email
    db.delete(user)
    db.commit()
    
    create_audit_log(
        db, current_user.id, "admin.users.delete", "user", user_id,
        description=f"Deleted user {user_email}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {"success": True, "message": "User deleted successfully"}

@app.get("/admin/billing", response_model=BillingSummaryResponse)
async def get_billing_summary(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get billing and payment summary"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    # Total revenue
    completed_payments = db.query(Payment).filter(Payment.status == "completed").all()
    total_revenue = sum(p.amount for p in completed_payments)
    
    # Revenue this month
    now = datetime.utcnow()
    first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    payments_this_month = [p for p in completed_payments if p.created_at >= first_day_this_month]
    revenue_this_month = sum(p.amount for p in payments_this_month)
    
    # Revenue last month
    if first_day_this_month.month == 1:
        first_day_last_month = first_day_this_month.replace(year=first_day_this_month.year - 1, month=12)
    else:
        first_day_last_month = first_day_this_month.replace(month=first_day_this_month.month - 1)
    last_day_last_month = first_day_this_month - timedelta(seconds=1)
    payments_last_month = [p for p in completed_payments if first_day_last_month <= p.created_at <= last_day_last_month]
    revenue_last_month = sum(p.amount for p in payments_last_month)
    
    # Pending payments
    pending_payments = db.query(Payment).filter(Payment.status == "pending").all()
    pending_amount = sum(p.amount for p in pending_payments)
    
    # Failed payments
    failed_payments = db.query(Payment).filter(Payment.status == "failed").all()
    failed_amount = sum(p.amount for p in failed_payments)
    
    # Refunded amount
    refunded_payments = db.query(Payment).filter(Payment.status == "refunded").all()
    refunded_amount = sum(p.amount for p in refunded_payments)
    
    # Revenue by payment method
    revenue_by_method = defaultdict(float)
    for payment in completed_payments:
        method = payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method)
        revenue_by_method[method] += payment.amount
    
    # Invoice summary
    invoices = db.query(Invoice).all()
    invoices_summary = {
        "total": len(invoices),
        "paid": len([i for i in invoices if i.status == "paid"]),
        "pending": len([i for i in invoices if i.status == "pending"]),
        "cancelled": len([i for i in invoices if i.status == "cancelled"])
    }
    
    create_audit_log(
        db, current_user.id, "admin.billing.view", "billing",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "total_revenue": total_revenue,
        "revenue_this_month": revenue_this_month,
        "revenue_last_month": revenue_last_month,
        "pending_payments": pending_amount,
        "failed_payments": failed_amount,
        "refunded_amount": refunded_amount,
        "revenue_by_payment_method": dict(revenue_by_method),
        "invoices_summary": invoices_summary
    }

@app.get("/admin/reports/usage")
async def get_usage_report(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    report_type: str = Query("summary")
):
    """Get usage statistics and reports"""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()
    
    # User registrations over time
    users = db.query(User).filter(
        User.created_at >= start_date,
        User.created_at <= end_date
    ).all()
    
    # Bookings over time
    bookings = db.query(Booking).filter(
        Booking.created_at >= start_date,
        Booking.created_at <= end_date
    ).all()
    
    # Payments over time
    payments = db.query(Payment).filter(
        Payment.created_at >= start_date,
        Payment.created_at <= end_date
    ).all()
    
    # Daily statistics
    daily_stats = defaultdict(lambda: {
        "users": 0,
        "bookings": 0,
        "payments": 0,
        "revenue": 0.0
    })
    
    for user in users:
        day_key = user.created_at.strftime("%Y-%m-%d")
        daily_stats[day_key]["users"] += 1
    
    for booking in bookings:
        day_key = booking.created_at.strftime("%Y-%m-%d")
        daily_stats[day_key]["bookings"] += 1
    
    for payment in payments:
        day_key = payment.created_at.strftime("%Y-%m-%d")
        daily_stats[day_key]["payments"] += 1
        if payment.status == "completed":
            daily_stats[day_key]["revenue"] += payment.amount
    
    create_audit_log(
        db, current_user.id, "admin.reports.view", "report",
        description=f"Viewed usage report: {report_type}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "success": True,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": {
            "total_users": len(users),
            "total_bookings": len(bookings),
            "total_payments": len(payments),
            "total_revenue": sum(p.amount for p in payments if p.status == "completed")
        },
        "daily_stats": dict(daily_stats)
    }

@app.get("/admin/health", response_model=SystemHealthResponse)
async def get_system_health(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system health monitoring data"""
    from datetime import datetime
    import time
    from database import check_database_connection
    from db_utils import DatabaseManager
    
    start_time = time.time()
    
    # Database health
    db_healthy = check_database_connection()
    db_manager = DatabaseManager()
    db_stats = db_manager.get_connection_pool_stats()
    table_stats = db_manager.get_table_stats()
    
    # API health (basic check)
    api_healthy = True
    try:
        # Simple query to test API
        db.query(User).limit(1).all()
    except:
        api_healthy = False
    
    # Services health
    services_health = {
        "database": "healthy" if db_healthy else "unhealthy",
        "api": "healthy" if api_healthy else "unhealthy",
        "payment_service": "healthy",  # Could check actual service status
        "auth_service": "healthy"
    }
    
    overall_status = "healthy" if (db_healthy and api_healthy) else "degraded"
    
    create_audit_log(
        db, current_user.id, "admin.health.view", "system",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return {
        "status": overall_status,
        "database": {
            "connected": db_healthy,
            "pool_stats": db_stats,
            "table_stats": table_stats
        },
        "api": {
            "status": "healthy" if api_healthy else "unhealthy",
            "response_time_ms": (time.time() - start_time) * 1000
        },
        "services": services_health,
        "uptime": time.time() - start_time,  # Simplified - should track actual uptime
        "timestamp": datetime.utcnow()
    }

@app.get("/admin/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    request: Request,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get audit logs with filtering"""
    from sqlalchemy import and_
    
    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for log in logs:
        user_email = None
        if log.user_id:
            user = db.query(User).filter(User.id == log.user_id).first()
            if user:
                user_email = user.email
        
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_email": user_email,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": log.created_at
        })
    
    create_audit_log(
        db, current_user.id, "admin.audit.view", "audit_log",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent")
    )
    
    return result

# ========== COMMUNICATION ENDPOINTS ==========

@app.post("/communication/chat/rooms", response_model=ChatRoomSchema)
async def create_chat_room(
    request_data: ChatRoomCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new chat room"""
    comm_service = CommunicationService()
    result = await comm_service.create_chat_room(
        room_type=request_data.room_type,
        user_id=current_user.id,
        provider_id=request_data.provider_id,
        guide_id=request_data.guide_id,
        name=request_data.name,
        db=db
    )
    return result["room"]

@app.get("/communication/chat/rooms", response_model=List[ChatRoomSchema])
async def get_chat_rooms(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all chat rooms for current user"""
    comm_service = CommunicationService()
    rooms = await comm_service.get_user_chat_rooms(current_user.id, db)
    return rooms

@app.post("/communication/chat/messages", response_model=MessageSchema)
async def send_message(
    request_data: MessageCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message in a chat room"""
    comm_service = CommunicationService()
    result = await comm_service.send_message(
        room_id=request_data.room_id,
        sender_id=current_user.id,
        content=request_data.content,
        message_type=request_data.message_type,
        translate_to=request_data.translate_to,
        db=db
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    message = result["message"]
    # Add sender email
    sender = db.query(User).filter(User.id == message.sender_id).first()
    return {
        "id": message.id,
        "room_id": message.room_id,
        "sender_id": message.sender_id,
        "sender_email": sender.email if sender else None,
        "content": message.content,
        "message_type": message.message_type,
        "translated_content": message.translated_content,
        "original_language": message.original_language,
        "translated_language": message.translated_language,
        "is_read": message.is_read,
        "created_at": message.created_at
    }

@app.get("/communication/chat/rooms/{room_id}/messages", response_model=List[MessageSchema])
async def get_messages(
    room_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get messages from a chat room"""
    comm_service = CommunicationService()
    result = await comm_service.get_messages(room_id, current_user.id, limit, offset, db)
    if not result.get("success"):
        raise HTTPException(status_code=403, detail=result.get("error"))
    
    messages = result["messages"]
    # Add sender emails
    result_messages = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first() if msg.sender_id else None
        result_messages.append({
            "id": msg.id,
            "room_id": msg.room_id,
            "sender_id": msg.sender_id,
            "sender_email": sender.email if sender else None,
            "content": msg.content,
            "message_type": msg.message_type,
            "translated_content": msg.translated_content,
            "original_language": msg.original_language,
            "translated_language": msg.translated_language,
            "is_read": msg.is_read,
            "created_at": msg.created_at
        })
    return result_messages

@app.post("/communication/ai/chat")
async def ai_chat(
    request_data: AIChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to AI chatbot"""
    comm_service = CommunicationService()
    result = await comm_service.send_ai_message(
        message=request_data.message,
        session_id=request_data.session_id,
        user_id=current_user.id,
        context=request_data.context,
        db=db
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/communication/ai/conversations/{session_id}", response_model=List[AIMessageSchema])
async def get_ai_conversation(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get AI conversation history"""
    comm_service = CommunicationService()
    messages = await comm_service.get_ai_conversation_history(session_id, current_user.id, db)
    return messages

@app.post("/communication/translate")
async def translate_text(
    request_data: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Translate text to target language"""
    comm_service = CommunicationService()
    result = await comm_service.translate_text(
        text=request_data.text,
        target_language=request_data.target_language,
        source_language=request_data.source_language
    )
    return result

@app.post("/communication/calls/initiate", response_model=CallSessionSchema)
async def initiate_call(
    request_data: CallInitiateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initiate a voice or video call"""
    comm_service = CommunicationService()
    result = await comm_service.initiate_call(
        call_type=request_data.call_type,
        initiator_id=current_user.id,
        recipient_id=request_data.recipient_id,
        guide_id=request_data.guide_id,
        room_id=request_data.room_id,
        db=db
    )
    return result["call"]

@app.patch("/communication/calls/{session_id}/status", response_model=CallSessionSchema)
async def update_call_status(
    session_id: str,
    status: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update call status"""
    comm_service = CommunicationService()
    result = await comm_service.update_call_status(session_id, status, db)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result["call"]

@app.post("/communication/broadcasts", response_model=BroadcastAlertSchema)
async def create_broadcast(
    request_data: BroadcastCreateRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a broadcast alert (Admin only)"""
    comm_service = CommunicationService()
    result = await comm_service.create_broadcast(
        alert_type=request_data.alert_type,
        priority=request_data.priority,
        title=request_data.title,
        message=request_data.message,
        target_audience=request_data.target_audience,
        target_user_ids=request_data.target_user_ids,
        expires_at=request_data.expires_at,
        created_by=current_user.id,
        db=db
    )
    return result["alert"]

@app.get("/communication/broadcasts", response_model=List[BroadcastAlertSchema])
async def get_broadcasts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get active broadcast alerts for current user"""
    comm_service = CommunicationService()
    alerts = await comm_service.get_active_broadcasts(
        user_id=current_user.id,
        user_role=current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        db=db
    )
    return alerts

@app.post("/communication/broadcasts/{alert_id}/view")
async def mark_broadcast_viewed(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark a broadcast alert as viewed"""
    comm_service = CommunicationService()
    result = await comm_service.mark_broadcast_viewed(alert_id, current_user.id, db)
    return result

@app.get("/communication/forums/categories", response_model=List[ForumCategorySchema])
async def get_forum_categories(db: Session = Depends(get_db)):
    """Get all forum categories"""
    comm_service = CommunicationService()
    categories = await comm_service.get_forum_categories(db)
    # Add post count
    from sqlalchemy import func
    result = []
    for cat in categories:
        post_count = db.query(func.count(ForumPost.id)).filter(
            ForumPost.category_id == cat.id
        ).scalar()
        result.append({
            "id": cat.id,
            "name": cat.name,
            "description": cat.description,
            "slug": cat.slug,
            "order": cat.order,
            "is_active": cat.is_active,
            "post_count": post_count
        })
    return result

@app.post("/communication/forums/posts", response_model=ForumPostSchema)
async def create_forum_post(
    request_data: ForumPostCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a forum post"""
    comm_service = CommunicationService()
    result = await comm_service.create_forum_post(
        category_id=request_data.category_id,
        author_id=current_user.id,
        title=request_data.title,
        content=request_data.content,
        db=db
    )
    post = result["post"]
    author = db.query(User).filter(User.id == post.author_id).first()
    return {
        "id": post.id,
        "category_id": post.category_id,
        "author_id": post.author_id,
        "author_email": author.email if author else None,
        "title": post.title,
        "content": post.content,
        "slug": post.slug,
        "is_pinned": post.is_pinned,
        "is_locked": post.is_locked,
        "view_count": post.view_count,
        "reply_count": post.reply_count,
        "last_reply_at": post.last_reply_at,
        "created_at": post.created_at
    }

@app.get("/communication/forums/posts", response_model=List[ForumPostSchema])
async def get_forum_posts(
    category_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get forum posts"""
    comm_service = CommunicationService()
    posts = await comm_service.get_forum_posts(category_id, limit, offset, db)
    result = []
    for post in posts:
        author = db.query(User).filter(User.id == post.author_id).first() if post.author_id else None
        result.append({
            "id": post.id,
            "category_id": post.category_id,
            "author_id": post.author_id,
            "author_email": author.email if author else None,
            "title": post.title,
            "content": post.content,
            "slug": post.slug,
            "is_pinned": post.is_pinned,
            "is_locked": post.is_locked,
            "view_count": post.view_count,
            "reply_count": post.reply_count,
            "last_reply_at": post.last_reply_at,
            "created_at": post.created_at
        })
    return result

@app.get("/communication/forums/posts/{post_id}", response_model=ForumPostSchema)
async def get_forum_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific forum post"""
    from models import ForumPost
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    post.view_count = (post.view_count or 0) + 1
    db.commit()
    db.refresh(post)
    
    author = db.query(User).filter(User.id == post.author_id).first() if post.author_id else None
    return {
        "id": post.id,
        "category_id": post.category_id,
        "author_id": post.author_id,
        "author_email": author.email if author else None,
        "title": post.title,
        "content": post.content,
        "slug": post.slug,
        "is_pinned": post.is_pinned,
        "is_locked": post.is_locked,
        "view_count": post.view_count,
        "reply_count": post.reply_count,
        "last_reply_at": post.last_reply_at,
        "created_at": post.created_at
    }

@app.get("/communication/forums/posts/{post_id}/replies", response_model=List[ForumReplySchema])
async def get_forum_replies(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get replies for a forum post"""
    from models import ForumReply
    replies = db.query(ForumReply).filter(ForumReply.post_id == post_id).order_by(
        ForumReply.created_at.asc()
    ).all()
    
    result = []
    for reply in replies:
        author = db.query(User).filter(User.id == reply.author_id).first() if reply.author_id else None
        result.append({
            "id": reply.id,
            "post_id": reply.post_id,
            "author_id": reply.author_id,
            "author_email": author.email if author else None,
            "parent_reply_id": reply.parent_reply_id,
            "content": reply.content,
            "is_solution": reply.is_solution,
            "created_at": reply.created_at
        })
    return result

@app.post("/communication/forums/replies", response_model=ForumReplySchema)
async def create_forum_reply(
    request_data: ForumReplyCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a forum reply"""
    comm_service = CommunicationService()
    result = await comm_service.create_forum_reply(
        post_id=request_data.post_id,
        author_id=current_user.id,
        content=request_data.content,
        parent_reply_id=request_data.parent_reply_id,
        db=db
    )
    reply = result["reply"]
    author = db.query(User).filter(User.id == reply.author_id).first()
    return {
        "id": reply.id,
        "post_id": reply.post_id,
        "author_id": reply.author_id,
        "author_email": author.email if author else None,
        "parent_reply_id": reply.parent_reply_id,
        "content": reply.content,
        "is_solution": reply.is_solution,
        "created_at": reply.created_at
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

