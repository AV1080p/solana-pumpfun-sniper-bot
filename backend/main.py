from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import Tour, Booking, Payment
from schemas import (
    TourSchema, BookingSchema, PaymentSchema, PaymentRequest,
    PaymentIntentRequest, PaymentIntentResponse, CryptoPaymentRequest,
    PaymentAddressRequest, PaymentAddressResponse, RefundRequest,
    TourCreateSchema, TourUpdateSchema, BookingUpdateSchema, ContactFormSchema
)
from services.payment_service import PaymentService
from services.solana_service import SolanaService
from services.crypto_service import CryptoService

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
async def create_tour(tour: TourCreateSchema, db: Session = Depends(get_db)):
    """Create a new tour (Admin only)"""
    db_tour = Tour(**tour.dict())
    db.add(db_tour)
    db.commit()
    db.refresh(db_tour)
    return db_tour

@app.put("/tours/{tour_id}", response_model=TourSchema)
async def update_tour(tour_id: int, tour: TourUpdateSchema, db: Session = Depends(get_db)):
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
async def delete_tour(tour_id: int, db: Session = Depends(get_db)):
    """Delete a tour (Admin only)"""
    db_tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not db_tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    
    db.delete(db_tour)
    db.commit()
    return {"message": "Tour deleted successfully"}

@app.get("/bookings", response_model=List[BookingSchema])
async def get_bookings(db: Session = Depends(get_db)):
    """Get all bookings with tour and payment information"""
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
async def create_booking(booking: BookingSchema, db: Session = Depends(get_db)):
    db_booking = Booking(**booking.dict())
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
async def update_booking(booking_id: int, booking: BookingUpdateSchema, db: Session = Depends(get_db)):
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

