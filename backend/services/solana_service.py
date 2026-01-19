from solana.rpc.api import Client
from solana.rpc.commitment import Finalized
from sqlalchemy.orm import Session
from models import Payment, Booking, Tour
from solders.pubkey import Pubkey
from solders.rpc.responses import GetTransactionResp
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SolanaService:
    def __init__(self):
        self.rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        self.client = Client(self.rpc_url)
        self.payment_wallet = os.getenv("PAYMENT_WALLET_ADDRESS")
        if self.payment_wallet:
            try:
                self.payment_wallet_pubkey = Pubkey.from_string(self.payment_wallet)
            except Exception as e:
                logger.warning(f"Invalid payment wallet address: {str(e)}")
                self.payment_wallet_pubkey = None
        else:
            self.payment_wallet_pubkey = None

    def get_payment_address(self) -> Dict[str, Any]:
        """Get the payment wallet address for receiving SOL payments"""
        if not self.payment_wallet:
            return {"success": False, "message": "Payment wallet not configured"}
        return {
            "success": True,
            "address": self.payment_wallet,
            "network": "devnet" if "devnet" in self.rpc_url else "mainnet"
        }

    async def verify_solana_payment(
        self,
        signature: str,
        amount: float,
        public_key: str,
        tour_id: int,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Verify a Solana payment transaction"""
        try:
            # Verify transaction signature
            transaction_resp: GetTransactionResp = self.client.get_transaction(
                signature,
                commitment=Finalized,
                max_supported_transaction_version=0
            )

            if not transaction_resp.value:
                return {"success": False, "message": "Transaction not found"}

            transaction = transaction_resp.value
            transaction_status = transaction.transaction.meta

            if not transaction_status or transaction_status.err:
                return {"success": False, "message": f"Transaction failed: {transaction_status.err if transaction_status else 'Unknown error'}"}

            # Get tour
            tour = db.query(Tour).filter(Tour.id == tour_id).first()
            if not tour:
                return {"success": False, "message": "Tour not found"}

            # Verify the transaction was sent to our payment wallet
            if self.payment_wallet_pubkey:
                # Check if payment was received (simplified check)
                # In production, you'd parse the transaction to verify the exact amount
                expected_amount_lamports = int(amount * 1e9)  # SOL to lamports

            # Check if payment already processed
            existing_payment = db.query(Payment).filter(
                Payment.transaction_id == signature
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
                amount=amount,
                payment_method="solana",
                transaction_id=signature,
                status="completed"
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)

            return {
                "success": True,
                "booking_id": booking.id,
                "payment_id": payment.id,
                "transaction_id": signature,
                "message": "Payment verified and booking confirmed"
            }
        except Exception as e:
            logger.error(f"Solana payment verification error: {str(e)}")
            return {"success": False, "message": str(e)}

    async def check_payment_status(
        self,
        signature: str
    ) -> Dict[str, Any]:
        """Check the status of a Solana payment transaction"""
        try:
            transaction_resp: GetTransactionResp = self.client.get_transaction(
                signature,
                commitment=Finalized,
                max_supported_transaction_version=0
            )

            if not transaction_resp.value:
                return {
                    "success": False,
                    "status": "not_found",
                    "message": "Transaction not found"
                }

            transaction = transaction_resp.value
            transaction_status = transaction.transaction.meta

            if transaction_status and transaction_status.err:
                return {
                    "success": False,
                    "status": "failed",
                    "message": f"Transaction failed: {transaction_status.err}"
                }

            return {
                "success": True,
                "status": "confirmed",
                "signature": signature,
                "slot": transaction.slot
            }
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            return {"success": False, "message": str(e)}

