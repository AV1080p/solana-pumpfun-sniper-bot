from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, Index, CheckConstraint
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
    user_email = Column(String(255), nullable=False, index=True)
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

