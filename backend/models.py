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

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

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
    
    # Relationships
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")

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

