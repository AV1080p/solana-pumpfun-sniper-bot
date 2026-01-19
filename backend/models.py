from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Index, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM, UUID
from database import Base
from datetime import datetime
import enum
import uuid

class PaymentMethod(str, enum.Enum):
    STRIPE = "stripe"
    SOLANA = "solana"
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"

class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"
    FACEBOOK = "facebook"
    APPLE = "apple"
    SAML = "saml"
    OIDC = "oidc"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class MFAMethod(str, enum.Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"

class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class InvitationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    auth_provider = Column(
        PG_ENUM(AuthProvider, name="auth_provider", create_type=True),
        default=AuthProvider.EMAIL,
        nullable=False,
        index=True
    )
    provider_id = Column(String(255), nullable=True, index=True)  # OAuth provider user ID
    role = Column(
        PG_ENUM(UserRole, name="user_role", create_type=True),
        default=UserRole.USER,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    mfa_secret = Column(String(255), nullable=True)  # TOTP secret
    backup_codes = Column(Text, nullable=True)  # JSON array of backup codes
    
    # Relationships
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    mfa_devices = relationship("MFADevice", back_populates="user", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="invited_by_user", foreign_keys="Invitation.invited_by")
    user_permissions = relationship("UserPermission", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_provider', 'auth_provider', 'provider_id'),
        Index('idx_users_uuid', 'uuid'),
    )

class Tour(Base):
    __tablename__ = "tours"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    price_sol = Column(Float, nullable=False)
    duration = Column(String(100))
    location = Column(String(255), index=True)
    image_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = relationship("Booking", back_populates="tour", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('price_sol >= 0', name='check_price_sol_positive'),
        Index('idx_tours_location', 'location'),
        Index('idx_tours_created_at', 'created_at'),
    )

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)  # Keep for backward compatibility
    booking_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    status = Column(
        PG_ENUM(BookingStatus, name="booking_status", create_type=True),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)

    tour = relationship("Tour", back_populates="bookings")
    user = relationship("User", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_bookings_user_email', 'user_email'),
        Index('idx_bookings_status', 'status'),
        Index('idx_bookings_booking_date', 'booking_date'),
        Index('idx_bookings_tour_status', 'tour_id', 'status'),
    )

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(
        PG_ENUM(PaymentMethod, name="payment_method", create_type=True),
        nullable=False,
        index=True
    )
    transaction_id = Column(String(255), unique=True, index=True)
    status = Column(
        PG_ENUM(PaymentStatus, name="payment_status", create_type=True),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))
    failure_reason = Column(Text)
    metadata = Column(Text)  # JSON string for additional payment data

    booking = relationship("Booking", back_populates="payments")

    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_payment_amount_positive'),
        Index('idx_payments_transaction_id', 'transaction_id'),
        Index('idx_payments_status', 'status'),
        Index('idx_payments_method_status', 'payment_method', 'status'),
        Index('idx_payments_created_at', 'created_at'),
    )

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    status = Column(String(50), default="pending", nullable=False, index=True)  # pending, paid, cancelled
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)

    user = relationship("User")
    booking = relationship("Booking")
    payment = relationship("Payment")

    __table_args__ = (
        CheckConstraint('amount >= 0', name='check_invoice_amount_positive'),
        CheckConstraint('total_amount >= 0', name='check_invoice_total_positive'),
        Index('idx_invoices_user_id', 'user_id'),
        Index('idx_invoices_status', 'status'),
        Index('idx_invoices_created_at', 'created_at'),
    )

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    feedback_type = Column(String(50), nullable=False, index=True)  # bug, feature, general, complaint
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    status = Column(String(50), default="open", nullable=False, index=True)  # open, in_progress, resolved, closed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    admin_response = Column(Text, nullable=True)

    user = relationship("User")

    __table_args__ = (
        Index('idx_feedback_user_id', 'user_id'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_status', 'status'),
        Index('idx_feedback_created_at', 'created_at'),
    )

class DataConsent(Base):
    """Track user consent for data processing (GDPR/CCPA compliance)"""
    __tablename__ = "data_consents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False, index=True)  # data_processing, marketing, analytics, third_party_sharing
    granted = Column(Boolean, default=False, nullable=False)
    granted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_consents_user_type', 'user_id', 'consent_type'),
        Index('idx_consents_granted', 'granted'),
    )

class DataRetentionLog(Base):
    """Log data retention policy actions for audit purposes"""
    __tablename__ = "data_retention_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    data_type = Column(String(50), nullable=False, index=True)  # booking, payment, invoice, feedback, user
    action = Column(String(50), nullable=False)  # delete, anonymize
    record_id = Column(Integer, nullable=True)  # ID of the affected record
    retention_days = Column(Integer, nullable=False)
    processed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON string for additional info
    
    __table_args__ = (
        Index('idx_retention_data_type', 'data_type'),
        Index('idx_retention_processed_at', 'processed_at'),
    )

class BackupRecord(Base):
    """Track database backups"""
    __tablename__ = "backup_records"
    
    id = Column(Integer, primary_key=True, index=True)
    backup_name = Column(String(255), nullable=False, unique=True, index=True)
    backup_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    encrypted = Column(Boolean, default=False, nullable=False)
    backup_type = Column(String(50), default="full", nullable=False)  # full, incremental
    status = Column(String(50), default="completed", nullable=False, index=True)  # completed, failed, in_progress
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional info
    
    __table_args__ = (
        Index('idx_backups_status', 'status'),
        Index('idx_backups_created_at', 'created_at'),
        Index('idx_backups_expires_at', 'expires_at'),
    )

# ========== AUTHENTICATION & SESSION MODELS ==========

class UserSession(Base):
    """User session management with refresh tokens"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    device_info = Column(String(255), nullable=True)  # Device name/type
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    status = Column(
        PG_ENUM(SessionStatus, name="session_status", create_type=True),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_sessions_user_status', 'user_id', 'status'),
        Index('idx_sessions_expires_at', 'expires_at'),
        Index('idx_sessions_token', 'session_token'),
    )

class MFADevice(Base):
    """MFA device registration (TOTP, SMS, etc.)"""
    __tablename__ = "mfa_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(
        PG_ENUM(MFAMethod, name="mfa_method", create_type=True),
        nullable=False,
        index=True
    )
    device_name = Column(String(255), nullable=False)  # e.g., "iPhone 12", "Google Authenticator"
    secret = Column(String(255), nullable=True)  # TOTP secret or phone number
    phone_number = Column(String(20), nullable=True)  # For SMS MFA
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="mfa_devices")
    
    __table_args__ = (
        Index('idx_mfa_user_method', 'user_id', 'method'),
        Index('idx_mfa_active', 'is_active'),
    )

class Invitation(Base):
    """User invitation system for onboarding"""
    __tablename__ = "invitations"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    role = Column(
        PG_ENUM(UserRole, name="invitation_role", create_type=True),
        default=UserRole.USER,
        nullable=False
    )
    status = Column(
        PG_ENUM(InvitationStatus, name="invitation_status", create_type=True),
        default=InvitationStatus.PENDING,
        nullable=False,
        index=True
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON for additional data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    invited_by_user = relationship("User", foreign_keys=[invited_by], back_populates="invitations")
    accepted_by_user = relationship("User", foreign_keys=[accepted_by_user_id])
    
    __table_args__ = (
        Index('idx_invitations_email_status', 'email', 'status'),
        Index('idx_invitations_token', 'token'),
        Index('idx_invitations_expires_at', 'expires_at'),
    )

class Permission(Base):
    """Granular permissions for RBAC"""
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "tours.create", "bookings.view"
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False, index=True)  # e.g., "tours", "bookings", "users"
    action = Column(String(50), nullable=False, index=True)  # e.g., "create", "read", "update", "delete"
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_permissions_resource_action', 'resource', 'action'),
    )

class RolePermission(Base):
    """Many-to-many relationship between roles and permissions"""
    __tablename__ = "role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role = Column(
        PG_ENUM(UserRole, name="role_permission_role", create_type=True),
        nullable=False,
        index=True
    )
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    permission = relationship("Permission")
    
    __table_args__ = (
        Index('idx_role_permissions_unique', 'role', 'permission_id', unique=True),
    )

class UserPermission(Base):
    """User-specific permissions (override role permissions)"""
    __tablename__ = "user_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    granted = Column(Boolean, default=True, nullable=False)  # True = grant, False = deny
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="user_permissions")
    permission = relationship("Permission")
    
    __table_args__ = (
        Index('idx_user_permissions_unique', 'user_id', 'permission_id', unique=True),
    )

class SAMLProvider(Base):
    """SAML 2.0 identity provider configuration"""
    __tablename__ = "saml_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    entity_id = Column(String(500), nullable=False)  # SAML entity ID
    sso_url = Column(String(500), nullable=False)  # SSO endpoint URL
    slo_url = Column(String(500), nullable=True)  # Single Logout URL
    x509_cert = Column(Text, nullable=False)  # X.509 certificate
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_url = Column(String(500), nullable=True)  # SAML metadata URL
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_saml_active', 'is_active'),
    )

class OIDCProvider(Base):
    """OpenID Connect provider configuration"""
    __tablename__ = "oidc_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    issuer = Column(String(500), nullable=False)  # OIDC issuer URL
    client_id = Column(String(255), nullable=False)
    client_secret = Column(String(255), nullable=False)
    authorization_endpoint = Column(String(500), nullable=False)
    token_endpoint = Column(String(500), nullable=False)
    userinfo_endpoint = Column(String(500), nullable=False)
    jwks_uri = Column(String(500), nullable=True)  # JWKS endpoint
    scopes = Column(String(255), default="openid email profile", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_oidc_active', 'is_active'),
    )

