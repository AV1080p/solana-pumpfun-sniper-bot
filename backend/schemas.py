from pydantic import BaseModel, EmailStr
from typing import Optional, List
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

# ========== SECURITY & COMPLIANCE SCHEMAS ==========

class DataExportRequest(BaseModel):
    format: Optional[str] = "json"  # json, csv
    user_id: int

class DataDeletionRequest(BaseModel):
    user_id: int
    anonymize: Optional[bool] = True  # If True, anonymize instead of delete

class ConsentUpdateRequest(BaseModel):
    consent_type: str  # data_processing, marketing, analytics, third_party_sharing
    granted: bool

class RetentionPolicyRequest(BaseModel):
    data_type: str  # booking, payment, invoice, feedback, user
    retention_days: int
    action: Optional[str] = "anonymize"  # delete, anonymize

class RetentionApplyRequest(BaseModel):
    data_type: Optional[str] = None  # If None, apply all policies
    dry_run: Optional[bool] = False

class BackupRequest(BaseModel):
    backup_name: Optional[str] = None
    encrypt: Optional[bool] = True

class RestoreRequest(BaseModel):
    backup_path: str
    drop_existing: Optional[bool] = False
    encrypted: Optional[bool] = False

# ========== MFA SCHEMAS ==========

class MFASetupRequest(BaseModel):
    device_name: str

class MFAVerifyRequest(BaseModel):
    code: str

class MFADisableRequest(BaseModel):
    password: str

class BackupCodeVerifyRequest(BaseModel):
    code: str

# ========== SESSION SCHEMAS ==========

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class SessionRevokeRequest(BaseModel):
    session_id: Optional[int] = None
    session_token: Optional[str] = None

# ========== INVITATION SCHEMAS ==========

class InvitationCreateRequest(BaseModel):
    email: EmailStr
    role: Optional[str] = "user"
    metadata: Optional[dict] = None

class InvitationAcceptRequest(BaseModel):
    token: str
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

# ========== SAML/OIDC SCHEMAS ==========

class SAMLInitiateRequest(BaseModel):
    provider_id: int

class OIDCInitiateRequest(BaseModel):
    provider_id: int
    state: Optional[str] = None

# ========== RBAC SCHEMAS ==========

class PermissionGrantRequest(BaseModel):
    user_id: int
    permission: str

class PermissionRevokeRequest(BaseModel):
    user_id: int
    permission: str

class PermissionCreateRequest(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None

# ========== ADMIN DASHBOARD SCHEMAS ==========

class AdminAnalyticsResponse(BaseModel):
    total_users: int
    total_bookings: int
    total_revenue: float
    total_payments: int
    active_users_30d: int
    new_users_30d: int
    revenue_by_month: dict
    bookings_by_status: dict
    payments_by_method: dict
    top_tours: list
    recent_activity: list

class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserListResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    total_bookings: int = 0
    total_spent: float = 0.0

    class Config:
        from_attributes = True

class BillingSummaryResponse(BaseModel):
    total_revenue: float
    revenue_this_month: float
    revenue_last_month: float
    pending_payments: float
    failed_payments: float
    refunded_amount: float
    revenue_by_payment_method: dict
    invoices_summary: dict

class UsageReportRequest(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    report_type: str = "summary"  # summary, detailed, export

class SystemHealthResponse(BaseModel):
    status: str
    database: dict
    api: dict
    services: dict
    uptime: float
    timestamp: datetime

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogFilterRequest(BaseModel):
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = 100
    offset: Optional[int] = 0

# ========== COMMUNICATION SCHEMAS ==========

class ChatRoomSchema(BaseModel):
    id: int
    room_type: str
    name: Optional[str] = None
    provider_id: Optional[int] = None
    guide_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageSchema(BaseModel):
    id: int
    room_id: int
    sender_id: Optional[int] = None
    sender_email: Optional[str] = None
    content: str
    message_type: str
    translated_content: Optional[str] = None
    original_language: Optional[str] = None
    translated_language: Optional[str] = None
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class MessageCreateRequest(BaseModel):
    room_id: int
    content: str
    message_type: Optional[str] = "text"
    translate_to: Optional[str] = None  # ISO language code

class ChatRoomCreateRequest(BaseModel):
    room_type: str  # "user_provider", "user_guide"
    provider_id: Optional[int] = None
    guide_id: Optional[int] = None
    name: Optional[str] = None

class AIConversationSchema(BaseModel):
    id: int
    user_id: int
    session_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AIMessageSchema(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AIChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict] = None

class CallSessionSchema(BaseModel):
    id: int
    call_type: str
    initiator_id: Optional[int] = None
    recipient_id: Optional[int] = None
    guide_id: Optional[int] = None
    session_id: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CallInitiateRequest(BaseModel):
    call_type: str  # "voice", "video"
    recipient_id: Optional[int] = None
    guide_id: Optional[int] = None
    room_id: Optional[int] = None

class BroadcastAlertSchema(BaseModel):
    id: int
    alert_type: str
    priority: str
    title: str
    message: str
    target_audience: str
    is_active: bool
    expires_at: Optional[datetime] = None
    created_at: datetime
    viewed: Optional[bool] = False
    
    class Config:
        from_attributes = True

class BroadcastCreateRequest(BaseModel):
    alert_type: str  # emergency, announcement, maintenance, info
    priority: str  # low, normal, high, critical
    title: str
    message: str
    target_audience: str  # all, users, providers, guides
    target_user_ids: Optional[List[int]] = None
    expires_at: Optional[datetime] = None

class ForumCategorySchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    slug: str
    order: int
    is_active: bool
    post_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

class ForumPostSchema(BaseModel):
    id: int
    category_id: int
    author_id: Optional[int] = None
    author_email: Optional[str] = None
    title: str
    content: str
    slug: Optional[str] = None
    is_pinned: bool
    is_locked: bool
    view_count: int
    reply_count: int
    last_reply_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ForumPostCreateRequest(BaseModel):
    category_id: int
    title: str
    content: str

class ForumReplySchema(BaseModel):
    id: int
    post_id: int
    author_id: Optional[int] = None
    author_email: Optional[str] = None
    parent_reply_id: Optional[int] = None
    content: str
    is_solution: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ForumReplyCreateRequest(BaseModel):
    post_id: int
    content: str
    parent_reply_id: Optional[int] = None

class TranslationRequest(BaseModel):
    text: str
    target_language: str  # ISO language code
    source_language: Optional[str] = None

# ========== SUPPORT SYSTEM SCHEMAS ==========

class SupportTicketCreateRequest(BaseModel):
    subject: str
    description: str
    category: str  # technical, billing, booking, general, emergency
    priority: Optional[str] = "normal"
    language: Optional[str] = "en"

class SupportTicketSchema(BaseModel):
    id: int
    ticket_number: str
    user_id: Optional[int] = None
    user_email: str
    subject: str
    description: str
    category: str
    priority: str
    status: str
    assigned_to: Optional[int] = None
    language: str
    resolution: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SupportMessageCreateRequest(BaseModel):
    ticket_id: int
    content: str
    attachments: Optional[List[str]] = None

class SupportMessageSchema(BaseModel):
    id: int
    ticket_id: int
    sender_id: Optional[int] = None
    sender_email: str
    sender_type: str
    content: str
    is_internal: bool
    attachments: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class SupportTicketUpdateRequest(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    resolution: Optional[str] = None

class FAQSchema(BaseModel):
    id: int
    category: str
    question: str
    answer: str
    language: str
    order: int
    view_count: int
    helpful_count: int
    not_helpful_count: int
    tags: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class FAQCreateRequest(BaseModel):
    category: str
    question: str
    answer: str
    language: Optional[str] = "en"
    order: Optional[int] = 0
    tags: Optional[List[str]] = None

class FAQUpdateRequest(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    answer: Optional[str] = None
    language: Optional[str] = None
    order: Optional[int] = None
    is_published: Optional[bool] = None
    tags: Optional[List[str]] = None

class FAQFeedbackRequest(BaseModel):
    faq_id: int
    helpful: bool  # True if helpful, False if not helpful

class TutorialSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    category: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    language: str
    order: int
    view_count: int
    tags: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TutorialCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    language: Optional[str] = "en"
    order: Optional[int] = 0
    tags: Optional[List[str]] = None

class SupportAgentSchema(BaseModel):
    id: int
    user_id: int
    languages: List[str]
    specialties: Optional[List[str]] = None
    availability_status: str
    rating: float
    total_resolved: int
    response_time_avg: Optional[float] = None
    
    class Config:
        from_attributes = True

class LocalSupportSchema(BaseModel):
    id: int
    location: str
    country: str
    city: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    languages: List[str]
    services: Optional[List[str]] = None
    availability_hours: Optional[dict] = None
    coordinates_lat: Optional[float] = None
    coordinates_lng: Optional[float] = None
    
    class Config:
        from_attributes = True

class AISupportRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict] = None

class AISupportResponse(BaseModel):
    success: bool
    message: str
    session_id: str
    suggestions: Optional[List[str]] = None
    suggested_faqs: Optional[List[int]] = None
    escalate_to_human: Optional[bool] = False
    confidence_score: Optional[float] = None

class SupportTicketSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    language: Optional[str] = "en"

# ========== PROVIDER BI DASHBOARD SCHEMAS ==========

class ServiceProviderSchema(BaseModel):
    id: int
    user_id: int
    business_name: str
    business_type: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ServiceProviderCreateRequest(BaseModel):
    business_name: str
    business_type: str  # tour_operator, guide, accommodation, activity
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class ReviewSchema(BaseModel):
    id: int
    tour_id: Optional[int] = None
    provider_id: Optional[int] = None
    user_id: Optional[int] = None
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    photos: Optional[List[str]] = None
    is_verified: bool
    helpful_count: int
    response: Optional[str] = None
    response_at: Optional[datetime] = None
    created_at: datetime
    user_name: Optional[str] = None
    tour_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class ReviewCreateRequest(BaseModel):
    tour_id: Optional[int] = None
    provider_id: Optional[int] = None
    booking_id: Optional[int] = None
    rating: int
    title: Optional[str] = None
    comment: Optional[str] = None
    photos: Optional[List[str]] = None

class ReviewResponseRequest(BaseModel):
    response: str

class MarketingCampaignSchema(BaseModel):
    id: int
    provider_id: int
    name: str
    campaign_type: str
    description: Optional[str] = None
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    spent: float
    status: str
    metrics: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MarketingCampaignCreateRequest(BaseModel):
    name: str
    campaign_type: str  # discount, promotion, email, social
    description: Optional[str] = None
    discount_percentage: Optional[float] = None
    discount_amount: Optional[float] = None
    start_date: datetime
    end_date: datetime
    budget: Optional[float] = None
    target_audience: Optional[dict] = None

class BookingAnalyticsResponse(BaseModel):
    success: bool
    period: dict
    total_bookings: int
    bookings_by_status: dict
    bookings_by_day: dict
    top_tours: List[dict]

class CustomerInsightsResponse(BaseModel):
    success: bool
    unique_customers: int
    actions_by_type: dict
    conversion_funnel: dict
    repeat_customer_rate: float
    repeat_customers: int
    total_customers: int
    customer_locations: dict

class RevenueAnalyticsResponse(BaseModel):
    success: bool
    total_revenue: float
    net_revenue: float
    platform_commission: float
    commission_rate: float
    revenue_by_method: dict
    revenue_by_day: dict
    revenue_by_tour: List[dict]
    total_transactions: int

class PerformanceMetricsResponse(BaseModel):
    success: bool
    total_reviews: int
    average_rating: float
    rating_distribution: dict
    total_bookings: int
    confirmed_bookings: int
    cancellation_rate: float
    total_views: int
    conversion_rate: float
    average_response_time_hours: Optional[float] = None
    response_rate: float

