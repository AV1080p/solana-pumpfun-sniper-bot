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

    class Config:
        from_attributes = True

class PaymentSchema(BaseModel):
    id: int
    booking_id: int
    amount: float
    payment_method: str
    transaction_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

class PaymentRequest(BaseModel):
    tour_id: int
    payment_method_id: str
    amount: float

