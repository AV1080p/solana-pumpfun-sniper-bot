import stripe
import os
from sqlalchemy.orm import Session
from models import Payment, Booking, Tour
from schemas import PaymentRequest

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentService:
    async def process_stripe_payment(
        self,
        payment_method_id: str,
        amount: float,
        tour_id: int,
        db: Session
    ):
        try:
            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_method_id,
                confirm=True,
                return_url="http://localhost:3000/bookings",
            )

            # Get tour
            tour = db.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return {"success": False, "message": "Tour not found"}

            # Create booking
            booking = Booking(
                tour_id=tour_id,
                status="confirmed"
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)

            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                amount=amount,
                payment_method="stripe",
                transaction_id=payment_intent.id,
                status="completed"
            )
            db.add(payment)
            db.commit()

            return {
                "success": True,
                "booking_id": booking.id,
                "payment_id": payment.id,
                "message": "Payment successful"
            }
        except stripe.error.StripeError as e:
            return {"success": False, "message": str(e)}

