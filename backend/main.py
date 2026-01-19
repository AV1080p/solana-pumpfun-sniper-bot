from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Query
import os
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import Tour, Booking, Payment
from schemas import (
    TourSchema, BookingSchema, PaymentSchema, PaymentRequest,
    PaymentIntentRequest, PaymentIntentResponse, CryptoPaymentRequest,
    PaymentAddressRequest, PaymentAddressResponse, RefundRequest,
    TourCreateSchema, TourUpdateSchema, BookingUpdateSchema, ContactFormSchema,
    UserRegisterSchema, UserLoginSchema, UserSchema, TokenResponse,
    OAuthTokenRequest, OAuthCallbackRequest
)
from services.payment_service import PaymentService
from services.solana_service import SolanaService
from services.crypto_service import CryptoService
from services.auth_service import AuthService
from auth import get_current_user, get_current_active_user, get_current_admin_user, get_optional_user
from models import User

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

@app.post("/auth/login", response_model=TokenResponse)
async def login(
    credentials: UserLoginSchema,
    db: Session = Depends(get_db)
):
    """Login with email/password"""
    auth_service = AuthService()
    result = await auth_service.login_user(
        email=credentials.email,
        password=credentials.password,
        db=db
    )
    return result

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
async def create_backup(backup_name: Optional[str] = None):
    """Create a database backup"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.backup_database(backup_name=backup_name)

@app.get("/database/backups")
async def list_backups():
    """List all available backups"""
    from db_utils import DatabaseManager
    manager = DatabaseManager()
    return manager.list_backups()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

