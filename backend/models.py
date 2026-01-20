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
    # Communication relationships
    chat_rooms_created = relationship("ChatRoom", foreign_keys="ChatRoom.created_by", cascade="all, delete-orphan")
    chat_participations = relationship("ChatParticipant", back_populates="user", cascade="all, delete-orphan")
    messages_sent = relationship("Message", back_populates="sender", cascade="all, delete-orphan")
    ai_conversations = relationship("AIConversation", back_populates="user", cascade="all, delete-orphan")
    calls_initiated = relationship("CallSession", foreign_keys="CallSession.initiator_id", cascade="all, delete-orphan")
    calls_received = relationship("CallSession", foreign_keys="CallSession.recipient_id")
    forum_posts = relationship("ForumPost", back_populates="author", cascade="all, delete-orphan")
    forum_replies = relationship("ForumReply", back_populates="author", cascade="all, delete-orphan")

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

class AuditLog(Base):
    """Audit log for tracking all admin and system activities"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # e.g., "user.create", "booking.update", "payment.refund"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "user", "booking", "payment"
    resource_id = Column(Integer, nullable=True, index=True)  # ID of the affected resource
    description = Column(Text, nullable=True)  # Human-readable description
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_created_at', 'created_at'),
    )

# ========== COMMUNICATION MODELS ==========

class ChatRoom(Base):
    """Chat rooms for conversations between users and providers"""
    __tablename__ = "chat_rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type = Column(String(50), nullable=False, index=True)  # "user_provider", "user_guide", "group"
    name = Column(String(255), nullable=True)  # For group chats
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # For provider chats
    guide_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)  # For guide chats
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = relationship("User", foreign_keys=[created_by])
    provider = relationship("User", foreign_keys=[provider_id])
    guide = relationship("User", foreign_keys=[guide_id])
    messages = relationship("Message", back_populates="room", cascade="all, delete-orphan")
    participants = relationship("ChatParticipant", back_populates="room", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_chat_room_type', 'room_type'),
        Index('idx_chat_room_provider', 'provider_id'),
    )

class ChatParticipant(Base):
    """Participants in chat rooms"""
    __tablename__ = "chat_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    room = relationship("ChatRoom", back_populates="participants")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_chat_participant_room_user', 'room_id', 'user_id', unique=True),
    )

class Message(Base):
    """Individual messages in chat rooms"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text", nullable=False)  # text, image, file, system
    translated_content = Column(Text, nullable=True)  # Translated version
    original_language = Column(String(10), nullable=True)  # ISO language code
    translated_language = Column(String(10), nullable=True)  # ISO language code
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON for file URLs, etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")
    
    __table_args__ = (
        Index('idx_messages_room_created', 'room_id', 'created_at'),
        Index('idx_messages_unread', 'room_id', 'is_read'),
    )

class AIConversation(Base):
    """AI chatbot conversations"""
    __tablename__ = "ai_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    context = Column(Text, nullable=True)  # JSON for conversation context
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_ai_conversation_user', 'user_id', 'created_at'),
    )

class AIMessage(Base):
    """Messages in AI conversations"""
    __tablename__ = "ai_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(Text, nullable=True)  # JSON for additional data
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    conversation = relationship("AIConversation", back_populates="messages")
    
    __table_args__ = (
        Index('idx_ai_messages_conversation_created', 'conversation_id', 'created_at'),
    )

class CallSession(Base):
    """Voice/video call sessions"""
    __tablename__ = "call_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    call_type = Column(String(20), nullable=False, index=True)  # voice, video
    initiator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    guide_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_rooms.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)  # WebRTC session ID
    status = Column(String(20), default="initiated", nullable=False, index=True)  # initiated, ringing, active, ended, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    recording_url = Column(String(500), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON for call metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    initiator = relationship("User", foreign_keys=[initiator_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    guide = relationship("User", foreign_keys=[guide_id])
    room = relationship("ChatRoom")
    
    __table_args__ = (
        Index('idx_call_sessions_status', 'status', 'created_at'),
    )

class BroadcastAlert(Base):
    """Broadcast alerts for emergencies and announcements"""
    __tablename__ = "broadcast_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(50), nullable=False, index=True)  # emergency, announcement, maintenance, info
    priority = Column(String(20), default="normal", nullable=False, index=True)  # low, normal, high, critical
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    target_audience = Column(String(50), default="all", nullable=False)  # all, users, providers, guides, specific
    target_user_ids = Column(Text, nullable=True)  # JSON array of user IDs for specific targeting
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    creator = relationship("User", foreign_keys=[created_by])
    views = relationship("BroadcastView", back_populates="alert", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_broadcast_active_expires', 'is_active', 'expires_at'),
    )

class BroadcastView(Base):
    """Track which users have viewed broadcast alerts"""
    __tablename__ = "broadcast_views"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("broadcast_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    viewed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    alert = relationship("BroadcastAlert", back_populates="views")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_broadcast_view_alert_user', 'alert_id', 'user_id', unique=True),
    )

class ForumCategory(Base):
    """Forum categories"""
    __tablename__ = "forum_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    posts = relationship("ForumPost", back_populates="category", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_forum_category_active', 'is_active', 'order'),
    )

class ForumPost(Base):
    """Forum posts/threads"""
    __tablename__ = "forum_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("forum_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    slug = Column(String(500), nullable=True, index=True)
    is_pinned = Column(Boolean, default=False, nullable=False, index=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    reply_count = Column(Integer, default=0, nullable=False)
    last_reply_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("ForumCategory", back_populates="posts")
    author = relationship("User")
    replies = relationship("ForumReply", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_forum_post_category_created', 'category_id', 'created_at'),
        Index('idx_forum_post_pinned', 'is_pinned', 'created_at'),
    )

class ForumReply(Base):
    """Forum post replies"""
    __tablename__ = "forum_replies"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("forum_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    parent_reply_id = Column(Integer, ForeignKey("forum_replies.id", ondelete="SET NULL"), nullable=True)  # For nested replies
    content = Column(Text, nullable=False)
    is_solution = Column(Boolean, default=False, nullable=False)  # Marked as solution
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    post = relationship("ForumPost", back_populates="replies")
    author = relationship("User")
    parent_reply = relationship("ForumReply", remote_side=[id])
    
    __table_args__ = (
        Index('idx_forum_reply_post_created', 'post_id', 'created_at'),
    )

# ========== SUPPORT SYSTEM MODELS ==========

class SupportTicket(Base):
    """Support ticket system for customer service"""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # technical, billing, booking, general, emergency
    priority = Column(String(20), default="normal", nullable=False, index=True)  # low, normal, high, urgent
    status = Column(String(50), default="open", nullable=False, index=True)  # open, assigned, in_progress, waiting, resolved, closed
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    language = Column(String(10), default="en", nullable=False)  # ISO language code
    ai_suggestions = Column(Text, nullable=True)  # JSON array of AI suggestions
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id])
    assignee = relationship("User", foreign_keys=[assigned_to])
    messages = relationship("SupportMessage", back_populates="ticket", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_tickets_user_status', 'user_id', 'status'),
        Index('idx_tickets_assignee_status', 'assigned_to', 'status'),
        Index('idx_tickets_priority_status', 'priority', 'status'),
        Index('idx_tickets_created_at', 'created_at'),
    )

class SupportMessage(Base):
    """Messages within support tickets"""
    __tablename__ = "support_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_email = Column(String(255), nullable=False)
    sender_type = Column(String(20), nullable=False, index=True)  # user, agent, ai, system
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)  # Internal notes not visible to user
    attachments = Column(Text, nullable=True)  # JSON array of attachment URLs
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    ticket = relationship("SupportTicket", back_populates="messages")
    sender = relationship("User")
    
    __table_args__ = (
        Index('idx_messages_ticket_created', 'ticket_id', 'created_at'),
    )

class FAQ(Base):
    """Frequently Asked Questions"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # booking, payment, account, technical, general
    question = Column(String(500), nullable=False)
    answer = Column(Text, nullable=False)
    language = Column(String(10), default="en", nullable=False, index=True)
    order = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON array of tags
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_faq_category_published', 'category', 'is_published'),
        Index('idx_faq_language_published', 'language', 'is_published'),
    )

class SupportAgent(Base):
    """Support agent information and availability"""
    __tablename__ = "support_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    languages = Column(Text, nullable=False)  # JSON array of language codes
    specialties = Column(Text, nullable=True)  # JSON array of specialties
    availability_status = Column(String(20), default="offline", nullable=False, index=True)  # online, offline, busy, away
    max_concurrent_tickets = Column(Integer, default=5, nullable=False)
    current_tickets_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=0.0, nullable=False)
    total_resolved = Column(Integer, default=0, nullable=False)
    response_time_avg = Column(Float, nullable=True)  # Average response time in minutes
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_agents_status_active', 'availability_status', 'is_active'),
    )

class Tutorial(Base):
    """Video tutorials and guides"""
    __tablename__ = "tutorials"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)  # getting_started, booking, payment, account, advanced
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    language = Column(String(10), default="en", nullable=False, index=True)
    order = Column(Integer, default=0, nullable=False)
    view_count = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False, index=True)
    tags = Column(Text, nullable=True)  # JSON array of tags
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_tutorials_category_published', 'category', 'is_published'),
        Index('idx_tutorials_language_published', 'language', 'is_published'),
    )

class LocalSupport(Base):
    """On-ground local support information"""
    __tablename__ = "local_support"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    city = Column(String(100), nullable=False, index=True)
    address = Column(Text, nullable=False)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    languages = Column(Text, nullable=False)  # JSON array of language codes
    services = Column(Text, nullable=True)  # JSON array of services offered
    availability_hours = Column(Text, nullable=True)  # JSON object with hours
    coordinates_lat = Column(Float, nullable=True)
    coordinates_lng = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_local_support_location', 'country', 'city'),
        Index('idx_local_support_active', 'is_active'),
    )

class AISupportConversation(Base):
    """AI support assistant conversations"""
    __tablename__ = "ai_support_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    context = Column(Text, nullable=True)  # JSON for conversation context
    user_intent = Column(String(100), nullable=True)  # Detected user intent
    suggested_actions = Column(Text, nullable=True)  # JSON array of suggested actions
    resolved = Column(Boolean, default=False, nullable=False)
    escalated_to_human = Column(Boolean, default=False, nullable=False)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    ticket = relationship("SupportTicket")
    messages = relationship("AISupportMessage", back_populates="conversation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_ai_support_user_session', 'user_id', 'session_id'),
    )

class AISupportMessage(Base):
    """Messages in AI support conversations"""
    __tablename__ = "ai_support_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("ai_support_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, index=True)  # user, assistant, system
    content = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=True)  # AI confidence in response
    suggested_faqs = Column(Text, nullable=True)  # JSON array of related FAQ IDs
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    
    conversation = relationship("AISupportConversation", back_populates="messages")
    
    __table_args__ = (
        Index('idx_ai_messages_conversation_created', 'conversation_id', 'created_at'),
    )

