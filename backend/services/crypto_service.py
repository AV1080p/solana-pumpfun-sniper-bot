from sqlalchemy.orm import Session
from models import Payment, Booking, Tour
from typing import Optional, Dict, Any
import os
import logging
import httpx
from decimal import Decimal

logger = logging.getLogger(__name__)

class CryptoService:
    """Service for handling multiple cryptocurrency payments"""
    
    def __init__(self):
        self.bitcoin_api_url = os.getenv("BITCOIN_API_URL", "https://blockstream.info/api")
        self.ethereum_rpc_url = os.getenv("ETHEREUM_RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/demo")
        self.payment_wallet_btc = os.getenv("PAYMENT_WALLET_BTC")
        self.payment_wallet_eth = os.getenv("PAYMENT_WALLET_ETH")

    async def get_bitcoin_payment_address(self) -> Dict[str, Any]:
        """Get Bitcoin payment address"""
        if not self.payment_wallet_btc:
            return {"success": False, "message": "Bitcoin wallet not configured"}
        return {
            "success": True,
            "address": self.payment_wallet_btc,
            "currency": "BTC",
            "network": "mainnet"
        }

    async def get_ethereum_payment_address(self) -> Dict[str, Any]:
        """Get Ethereum payment address"""
        if not self.payment_wallet_eth:
            return {"success": False, "message": "Ethereum wallet not configured"}
        return {
            "success": True,
            "address": self.payment_wallet_eth,
            "currency": "ETH",
            "network": "sepolia" if "sepolia" in self.ethereum_rpc_url else "mainnet"
        }

    async def verify_bitcoin_payment(
        self,
        tx_hash: str,
        amount: float,
        tour_id: int,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Verify a Bitcoin payment transaction"""
        try:
            async with httpx.AsyncClient() as client:
                # Get transaction details from block explorer
                response = await client.get(
                    f"{self.bitcoin_api_url}/tx/{tx_hash}"
                )
                
                if response.status_code != 200:
                    return {"success": False, "message": "Transaction not found"}

                tx_data = response.json()
                
                # Verify transaction is confirmed
                if tx_data.get("status", {}).get("block_height") is None:
                    return {"success": False, "message": "Transaction not confirmed"}

                # Get tour
                tour = db.query(Tour).filter(Tour.id == tour_id).first()
                if not tour:
                    return {"success": False, "message": "Tour not found"}

                # Check if payment already processed
                existing_payment = db.query(Payment).filter(
                    Payment.transaction_id == tx_hash
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
                    payment_method="bitcoin",
                    transaction_id=tx_hash,
                    status="completed"
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)

                return {
                    "success": True,
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "transaction_id": tx_hash,
                    "message": "Bitcoin payment verified and booking confirmed"
                }
        except Exception as e:
            logger.error(f"Bitcoin payment verification error: {str(e)}")
            return {"success": False, "message": str(e)}

    async def verify_ethereum_payment(
        self,
        tx_hash: str,
        amount: float,
        tour_id: int,
        user_email: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Verify an Ethereum payment transaction"""
        try:
            # Use Ethereum RPC to get transaction receipt
            async with httpx.AsyncClient() as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_getTransactionReceipt",
                    "params": [tx_hash],
                    "id": 1
                }
                response = await client.post(self.ethereum_rpc_url, json=payload)
                
                if response.status_code != 200:
                    return {"success": False, "message": "Failed to fetch transaction"}

                result = response.json()
                
                if not result.get("result"):
                    return {"success": False, "message": "Transaction not found"}

                receipt = result["result"]
                
                # Check if transaction was successful
                if receipt.get("status") != "0x1":
                    return {"success": False, "message": "Transaction failed"}

                # Get tour
                tour = db.query(Tour).filter(Tour.id == tour_id).first()
                if not tour:
                    return {"success": False, "message": "Tour not found"}

                # Check if payment already processed
                existing_payment = db.query(Payment).filter(
                    Payment.transaction_id == tx_hash
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
                    payment_method="ethereum",
                    transaction_id=tx_hash,
                    status="completed"
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)

                return {
                    "success": True,
                    "booking_id": booking.id,
                    "payment_id": payment.id,
                    "transaction_id": tx_hash,
                    "message": "Ethereum payment verified and booking confirmed"
                }
        except Exception as e:
            logger.error(f"Ethereum payment verification error: {str(e)}")
            return {"success": False, "message": str(e)}

    async def check_crypto_payment_status(
        self,
        tx_hash: str,
        currency: str
    ) -> Dict[str, Any]:
        """Check the status of a cryptocurrency payment"""
        try:
            if currency.lower() == "btc":
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.bitcoin_api_url}/tx/{tx_hash}"
                    )
                    if response.status_code == 200:
                        tx_data = response.json()
                        return {
                            "success": True,
                            "status": "confirmed" if tx_data.get("status", {}).get("block_height") else "pending",
                            "confirmations": tx_data.get("status", {}).get("block_height", 0)
                        }
            elif currency.lower() in ["eth", "ethereum"]:
                async with httpx.AsyncClient() as client:
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "eth_getTransactionReceipt",
                        "params": [tx_hash],
                        "id": 1
                    }
                    response = await client.post(self.ethereum_rpc_url, json=payload)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("result"):
                            return {
                                "success": True,
                                "status": "confirmed" if result["result"].get("status") == "0x1" else "failed"
                            }
            
            return {"success": False, "message": "Transaction not found"}
        except Exception as e:
            logger.error(f"Error checking crypto payment status: {str(e)}")
            return {"success": False, "message": str(e)}

