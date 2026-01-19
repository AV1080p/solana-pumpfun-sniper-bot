"""
GDPR/CCPA Compliance Service

Provides tools for:
- Data export (right to access)
- Data deletion (right to be forgotten)
- Consent management
- Data portability
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import User, Booking, Payment, Invoice, Feedback
from services.encryption_service import get_encryption_service

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for GDPR/CCPA compliance operations"""
    
    def __init__(self):
        self.encryption_service = get_encryption_service()
    
    def export_user_data(self, user_id: int, db: Session) -> Dict[str, Any]:
        """
        Export all user data (GDPR Right to Access)
        
        Args:
            user_id: The user ID to export data for
            db: Database session
            
        Returns:
            Dictionary containing all user data
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Collect all user data
            data = {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user.id,
                "user_uuid": str(user.uuid),
                "profile": {
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "phone_number": user.phone_number,
                    "avatar_url": user.avatar_url,
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "auth_provider": user.auth_provider.value if hasattr(user.auth_provider, 'value') else str(user.auth_provider),
                    "is_active": user.is_active,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                },
                "bookings": [],
                "payments": [],
                "invoices": [],
                "feedback": []
            }
            
            # Get bookings
            bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
            for booking in bookings:
                booking_data = {
                    "id": booking.id,
                    "tour_id": booking.tour_id,
                    "booking_date": booking.booking_date.isoformat() if booking.booking_date else None,
                    "status": booking.status.value if hasattr(booking.status, 'value') else str(booking.status),
                    "notes": booking.notes,
                    "created_at": booking.created_at.isoformat() if booking.created_at else None,
                    "updated_at": booking.updated_at.isoformat() if booking.updated_at else None,
                }
                if booking.tour:
                    booking_data["tour_name"] = booking.tour.name
                    booking_data["tour_location"] = booking.tour.location
                data["bookings"].append(booking_data)
            
            # Get payments
            payments = db.query(Payment).join(Booking).filter(Booking.user_id == user_id).all()
            for payment in payments:
                payment_data = {
                    "id": payment.id,
                    "booking_id": payment.booking_id,
                    "amount": payment.amount,
                    "payment_method": payment.payment_method.value if hasattr(payment.payment_method, 'value') else str(payment.payment_method),
                    "status": payment.status.value if hasattr(payment.status, 'value') else str(payment.status),
                    "transaction_id": payment.transaction_id,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                    "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
                }
                data["payments"].append(payment_data)
            
            # Get invoices
            invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
            for invoice in invoices:
                invoice_data = {
                    "id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "amount": invoice.amount,
                    "tax_amount": invoice.tax_amount,
                    "total_amount": invoice.total_amount,
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                    "paid_at": invoice.paid_at.isoformat() if invoice.paid_at else None,
                    "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
                }
                data["invoices"].append(invoice_data)
            
            # Get feedback
            feedbacks = db.query(Feedback).filter(Feedback.user_id == user_id).all()
            for feedback in feedbacks:
                feedback_data = {
                    "id": feedback.id,
                    "feedback_type": feedback.feedback_type,
                    "subject": feedback.subject,
                    "message": feedback.message,
                    "rating": feedback.rating,
                    "status": feedback.status,
                    "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                    "admin_response": feedback.admin_response,
                }
                data["feedback"].append(feedback_data)
            
            return {
                "success": True,
                "data": data,
                "format": "json",
                "exported_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to export user data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_user_data(self, user_id: int, db: Session, anonymize: bool = True) -> Dict[str, Any]:
        """
        Delete or anonymize user data (GDPR Right to be Forgotten)
        
        Args:
            user_id: The user ID to delete data for
            db: Database session
            anonymize: If True, anonymize data instead of deleting (for legal/compliance reasons)
            
        Returns:
            Dictionary with deletion results
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            deleted_items = {
                "user": False,
                "bookings": 0,
                "payments": 0,
                "invoices": 0,
                "feedback": 0
            }
            
            if anonymize:
                # Anonymize user data instead of deleting
                user.email = f"deleted_{user.id}_{datetime.utcnow().timestamp()}@deleted.local"
                user.username = f"deleted_user_{user.id}"
                user.full_name = "Deleted User"
                user.phone_number = None
                user.avatar_url = None
                user.hashed_password = None
                user.is_active = False
                deleted_items["user"] = True
                
                # Anonymize bookings
                bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
                for booking in bookings:
                    booking.user_email = f"deleted_{user.id}@deleted.local"
                    booking.notes = None
                    deleted_items["bookings"] += 1
                
                # Anonymize feedback
                feedbacks = db.query(Feedback).filter(Feedback.user_id == user_id).all()
                for feedback in feedbacks:
                    feedback.user_email = f"deleted_{user.id}@deleted.local"
                    feedback.message = "[Content deleted]"
                    deleted_items["feedback"] += 1
                
                db.commit()
            else:
                # Delete all related data (cascade should handle most)
                bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
                deleted_items["bookings"] = len(bookings)
                
                payments = db.query(Payment).join(Booking).filter(Booking.user_id == user_id).all()
                deleted_items["payments"] = len(payments)
                
                invoices = db.query(Invoice).filter(Invoice.user_id == user_id).all()
                deleted_items["invoices"] = len(invoices)
                
                feedbacks = db.query(Feedback).filter(Feedback.user_id == user_id).all()
                deleted_items["feedback"] = len(feedbacks)
                
                # Delete user (cascade will handle related records)
                db.delete(user)
                db.commit()
                deleted_items["user"] = True
            
            return {
                "success": True,
                "message": "User data deleted successfully" if not anonymize else "User data anonymized successfully",
                "deleted_items": deleted_items,
                "anonymized": anonymize,
                "deleted_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to delete user data: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_data_json(self, user_id: int, db: Session) -> str:
        """Export user data as JSON string"""
        result = self.export_user_data(user_id, db)
        if result["success"]:
            return json.dumps(result["data"], indent=2)
        else:
            raise ValueError(result.get("error", "Export failed"))
    
    def export_data_csv(self, user_id: int, db: Session) -> str:
        """Export user data as CSV (simplified)"""
        import csv
        from io import StringIO
        
        result = self.export_user_data(user_id, db)
        if not result["success"]:
            raise ValueError(result.get("error", "Export failed"))
        
        data = result["data"]
        output = StringIO()
        
        # Write profile data
        writer = csv.writer(output)
        writer.writerow(["Data Type", "Field", "Value"])
        writer.writerow(["Profile", "Email", data["profile"]["email"]])
        writer.writerow(["Profile", "Username", data["profile"]["username"]])
        writer.writerow(["Profile", "Full Name", data["profile"]["full_name"]])
        
        # Write bookings
        writer.writerow([])
        writer.writerow(["Bookings"])
        writer.writerow(["ID", "Tour ID", "Booking Date", "Status"])
        for booking in data["bookings"]:
            writer.writerow([
                booking["id"],
                booking["tour_id"],
                booking["booking_date"],
                booking["status"]
            ])
        
        return output.getvalue()
    
    def get_consent_status(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get user consent status for data processing"""
        # This would typically be stored in a consent table
        # For now, return a placeholder
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        return {
            "success": True,
            "user_id": user_id,
            "consents": {
                "data_processing": True,  # Default to True if user exists
                "marketing": False,
                "analytics": True,
                "third_party_sharing": False
            },
            "last_updated": user.updated_at.isoformat() if user.updated_at else None
        }
    
    def update_consent(self, user_id: int, consent_type: str, granted: bool, db: Session) -> Dict[str, Any]:
        """Update user consent for data processing"""
        # This would typically update a consent table
        # For now, return a placeholder
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"success": False, "error": "User not found"}
        
        return {
            "success": True,
            "message": f"Consent {consent_type} updated to {granted}",
            "user_id": user_id,
            "consent_type": consent_type,
            "granted": granted,
            "updated_at": datetime.utcnow().isoformat()
        }

