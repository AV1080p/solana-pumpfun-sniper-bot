import stripe
import os
from sqlalchemy.orm import Session
from models import Payment, Booking, Tour
from schemas import PaymentRequest
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentService:
    def __init__(self):
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key

    async def create_payment_intent(
        self,
        amount: float,
        currency: str = "usd",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for debit/credit card payments"""
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                payment_method_types=["card"],
                metadata=metadata or {},
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never"
                }
            )
            return {
                "success": True,
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {"success": False, "message": str(e)}

    async def process_stripe_payment(
        self,
        payment_method_id: str,
        amount: float,
        tour_id: int,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Process a Stripe payment with debit/credit card"""
        try:
            # Get tour
            tour = db.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return {"success": False, "message": "Tour not found"}

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency="usd",
                payment_method=payment_method_id,
                confirm=True,
                return_url="http://localhost:3000/bookings",
                metadata={
                    "tour_id": str(tour_id),
                    "user_email": user_email or ""
                }
            )

            # Check payment status
            if payment_intent.status == "succeeded":
                # Create booking
                booking = Booking(
                    tour_id=tour_id,
                    user_email=user_email,
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
                db.refresh(payment)

                return {
                    "success": True,
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "transaction_id": payment_intent.id,
                    "message": "Payment successful"
                }
            else:
                return {
                    "success": False,
                    "message": f"Payment status: {payment_intent.status}",
                    "payment_intent_id": payment_intent.id
                }
        except stripe.error.CardError as e:
            logger.error(f"Card error: {str(e)}")
            return {"success": False, "message": f"Card error: {e.user_message}"}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {"success": False, "message": f"Payment processing failed: {str(e)}"}

    async def confirm_payment_intent(
        self,
        payment_intent_id: str,
        tour_id: int,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Confirm a payment intent after client-side confirmation"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if payment_intent.status == "succeeded":
                # Get tour
                tour = db.query(Tour).filter(Tour.id == tour_id).first()
                if not tour:
                    return {"success": False, "message": "Tour not found"}

                # Check if payment already processed
                existing_payment = db.query(Payment).filter(
                    Payment.transaction_id == payment_intent_id
                ).first()

                if existing_payment:
                    return {
                        "success": True,
                        "message": "Payment already processed",
                        "payment_id": existing_payment.id
                    }

                # Create booking
                booking = Booking(
                    tour_id=tour_id,
                    user_email=user_email,
                    status="confirmed"
                )
                db.add(booking)
                db.commit()
                db.refresh(booking)

                # Create payment record
                payment = Payment(
                    booking_id=booking.id,
                    amount=payment_intent.amount / 100,  # Convert from cents
                    payment_method="stripe",
                    transaction_id=payment_intent_id,
                    status="completed"
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)

                return {
                    "success": True,
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "message": "Payment confirmed"
                }
            else:
                return {
                    "success": False,
                    "message": f"Payment status: {payment_intent.status}"
                }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {"success": False, "message": str(e)}

    async def refund_payment(
        self,
        payment_id: int,
        amount: Optional[float] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Refund a Stripe payment"""
        try:
            payment = db.query(Payment).filter(Payment.id == payment_id).first()
            if not payment:
                return {"success": False, "message": "Payment not found"}

            if payment.payment_method != "stripe":
                return {"success": False, "message": "Refund only available for Stripe payments"}

            if payment.status != "completed":
                return {"success": False, "message": "Can only refund completed payments"}

            # Create refund
            refund_amount = int((amount or payment.amount) * 100)
            refund = stripe.Refund.create(
                payment_intent=payment.transaction_id,
                amount=refund_amount
            )

            # Update payment status
            payment.status = "refunded"
            db.commit()

            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount / 100,
                "message": "Refund processed successfully"
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe refund error: {str(e)}")
            return {"success": False, "message": str(e)}

    def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return {"success": False, "message": "Invalid payload"}
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {"success": False, "message": "Invalid signature"}

        # Handle the event
        if event["type"] == "payment_intent.succeeded":
            payment_intent = event["data"]["object"]
            logger.info(f"Payment succeeded: {payment_intent['id']}")
            return {
                "success": True,
                "event": "payment_intent.succeeded",
                "payment_intent_id": payment_intent["id"]
            }
        elif event["type"] == "payment_intent.payment_failed":
            payment_intent = event["data"]["object"]
            logger.warning(f"Payment failed: {payment_intent['id']}")
            return {
                "success": True,
                "event": "payment_intent.payment_failed",
                "payment_intent_id": payment_intent["id"]
            }

        return {"success": True, "event": event["type"]}

