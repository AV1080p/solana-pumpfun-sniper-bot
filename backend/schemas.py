from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TourSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    price_sol: float
    duration: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class BookingSchema(BaseModel):
    id: Optional[int] = None
    tour_id: int
    user_email: Optional[str] = None
    booking_date: Optional[datetime] = None
    status: Optional[str] = "pending"
    notes: Optional[str] = None
    tour_name: Optional[str] = None
    payment_method: Optional[str] = None
    amount: Optional[float] = None

    class Config:
        from_attributes = True

class PaymentSchema(BaseModel):
    id: int
    booking_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    status: str
    completed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Optional[str] = None

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    tour_id: int
    payment_method_id: str
    amount: float
    user_email: Optional[str] = None

class PaymentIntentRequest(BaseModel):
    tour_id: int
    amount: float
    currency: Optional[str] = "usd"
    user_email: Optional[str] = None

class PaymentIntentResponse(BaseModel):
    success: bool
    client_secret: Optional[str] = None
    payment_intent_id: Optional[str] = None
    message: Optional[str] = None

class CryptoPaymentRequest(BaseModel):
    tour_id: int
    transaction_hash: str
    amount: float
    currency: str  # "solana", "bitcoin", "ethereum"
    public_key: Optional[str] = None
    user_email: Optional[str] = None

class PaymentAddressRequest(BaseModel):
    currency: str  # "solana", "bitcoin", "ethereum"

class PaymentAddressResponse(BaseModel):
    success: bool
    address: Optional[str] = None
    currency: Optional[str] = None
    network: Optional[str] = None
    message: Optional[str] = None

class RefundRequest(BaseModel):
    payment_id: int
    amount: Optional[float] = None

class TourCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    price_sol: float
    duration: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None

class TourUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_sol: Optional[float] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    image_url: Optional[str] = None

class BookingUpdateSchema(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class ContactFormSchema(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

# ========== AUTHENTICATION SCHEMAS ==========

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class UserSchema(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    is_verified: bool
    auth_provider: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str
    user: UserSchema

class OAuthTokenRequest(BaseModel):
    token: str
    provider: str  # "google", "github", etc.

class OAuthCallbackRequest(BaseModel):
    code: str
    provider: str

# ========== CUSTOMER DASHBOARD SCHEMAS ==========

class AccountSettingsUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordUpdateSchema(BaseModel):
    current_password: str
    new_password: str

class InvoiceSchema(BaseModel):
    id: int
    invoice_number: str
    user_id: int
    booking_id: Optional[int] = None
    payment_id: Optional[int] = None
    amount: float
    tax_amount: float
    total_amount: float
    currency: str
    status: str
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class UsageAnalyticsSchema(BaseModel):
    total_bookings: int
    total_spent: float
    favorite_destinations: list
    booking_trends: dict
    payment_methods_used: dict
    recent_activity: list

class FeedbackSchema(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: str
    feedback_type: str
    subject: str
    message: str
    rating: Optional[int] = None
    status: str
    created_at: datetime
    admin_response: Optional[str] = None

    class Config:
        from_attributes = True

class FeedbackCreateSchema(BaseModel):
    feedback_type: str  # bug, feature, general, complaint
    subject: str
    message: str
    rating: Optional[int] = None

