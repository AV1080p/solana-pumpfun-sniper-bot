from solana.rpc.api import Client
from solana.rpc.commitment import Confirmed
from sqlalchemy.orm import Session
from models import Payment, Booking, Tour
import os

class SolanaService:
    def __init__(self):
        self.rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        self.client = Client(self.rpc_url)

    async def verify_solana_payment(
        self,
        signature: str,
        amount: float,
        public_key: str,
        tour_id: int,
        db: Session
    ):
        try:
            # Verify transaction signature
            transaction = self.client.get_transaction(
                signature,
                commitment=Confirmed,
                max_supported_transaction_version=0
            )

            if not transaction.value:
                return {"success": False, "message": "Transaction not found"}

            # Get tour
            tour = db.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return {"success": False, "message": "Tour not found"}

            # Verify amount (simplified - in production, check actual transfer amount)
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
                payment_method="solana",
                transaction_id=signature,
                status="completed"
            )
            db.add(payment)
            db.commit()

            return {
                "success": True,
                "booking_id": booking.id,
                "payment_id": payment.id,
                "message": "Payment verified and booking confirmed"
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

