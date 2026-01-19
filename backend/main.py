from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
from dotenv import load_dotenv

from database import SessionLocal, engine, Base
from models import Tour, Booking, Payment
from schemas import TourSchema, BookingSchema, PaymentSchema, PaymentRequest
from services.payment_service import PaymentService
from services.solana_service import SolanaService

load_dotenv()

Base.metadata.create_all(bind=engine)

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

@app.get("/bookings", response_model=List[BookingSchema])
async def get_bookings(db: Session = Depends(get_db)):
    bookings = db.query(Booking).all()
    return bookings

@app.post("/bookings", response_model=BookingSchema)
async def create_booking(booking: BookingSchema, db: Session = Depends(get_db)):
    db_booking = Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking

@app.post("/payments/stripe")
async def process_stripe_payment(payment_request: PaymentRequest, db: Session = Depends(get_db)):
    try:
        payment_service = PaymentService()
        result = await payment_service.process_stripe_payment(
            payment_method_id=payment_request.payment_method_id,
            amount=payment_request.amount,
            tour_id=payment_request.tour_id,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/payments/solana")
async def process_solana_payment(payment_data: dict, db: Session = Depends(get_db)):
    try:
        solana_service = SolanaService()
        result = await solana_service.verify_solana_payment(
            signature=payment_data.get("signature"),
            amount=payment_data.get("amount"),
            public_key=payment_data.get("public_key"),
            tour_id=payment_data.get("tour_id"),
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

