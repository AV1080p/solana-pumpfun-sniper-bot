"""
Data Retention Policy Service

Automatically manages data retention policies:
- Delete/anonymize data older than retention period
- Configurable retention periods per data type
- Audit logging of retention actions
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import User, Booking, Payment, Invoice, Feedback
from services.compliance_service import ComplianceService

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """Defines a data retention policy"""
    
    def __init__(self, data_type: str, retention_days: int, action: str = "anonymize"):
        """
        Args:
            data_type: Type of data (e.g., 'booking', 'payment', 'feedback')
            retention_days: Number of days to retain data
            action: Action to take after retention period ('delete' or 'anonymize')
        """
        self.data_type = data_type
        self.retention_days = retention_days
        self.action = action  # 'delete' or 'anonymize'
    
    def get_cutoff_date(self) -> datetime:
        """Get the cutoff date before which data should be processed"""
        return datetime.utcnow() - timedelta(days=self.retention_days)


class RetentionService:
    """Service for managing data retention policies"""
    
    def __init__(self):
        self.compliance_service = ComplianceService()
        self.policies: Dict[str, RetentionPolicy] = {}
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default retention policies"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # Default policies (can be overridden via environment variables)
        self.policies = {
            "booking": RetentionPolicy(
                "booking",
                int(os.getenv("RETENTION_BOOKING_DAYS", "2555")),  # 7 years default
                os.getenv("RETENTION_BOOKING_ACTION", "anonymize")
            ),
            "payment": RetentionPolicy(
                "payment",
                int(os.getenv("RETENTION_PAYMENT_DAYS", "2555")),  # 7 years (legal requirement)
                os.getenv("RETENTION_PAYMENT_ACTION", "anonymize")
            ),
            "invoice": RetentionPolicy(
                "invoice",
                int(os.getenv("RETENTION_INVOICE_DAYS", "2555")),  # 7 years
                os.getenv("RETENTION_INVOICE_ACTION", "anonymize")
            ),
            "feedback": RetentionPolicy(
                "feedback",
                int(os.getenv("RETENTION_FEEDBACK_DAYS", "365")),  # 1 year
                os.getenv("RETENTION_FEEDBACK_ACTION", "delete")
            ),
            "user": RetentionPolicy(
                "user",
                int(os.getenv("RETENTION_USER_DAYS", "3650")),  # 10 years for inactive users
                os.getenv("RETENTION_USER_ACTION", "anonymize")
            ),
        }
    
    def add_policy(self, policy: RetentionPolicy):
        """Add or update a retention policy"""
        self.policies[policy.data_type] = policy
    
    def get_policy(self, data_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for a data type"""
        return self.policies.get(data_type)
    
    def apply_retention_policy(self, data_type: str, db: Session, dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply retention policy for a specific data type
        
        Args:
            data_type: Type of data to process
            db: Database session
            dry_run: If True, only report what would be done without making changes
            
        Returns:
            Dictionary with results
        """
        policy = self.get_policy(data_type)
        if not policy:
            return {
                "success": False,
                "error": f"No retention policy found for {data_type}"
            }
        
        cutoff_date = policy.get_cutoff_date()
        results = {
            "data_type": data_type,
            "policy": {
                "retention_days": policy.retention_days,
                "action": policy.action,
                "cutoff_date": cutoff_date.isoformat()
            },
            "processed_count": 0,
            "dry_run": dry_run,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        try:
            if data_type == "booking":
                results.update(self._process_bookings(cutoff_date, policy, db, dry_run))
            elif data_type == "payment":
                results.update(self._process_payments(cutoff_date, policy, db, dry_run))
            elif data_type == "invoice":
                results.update(self._process_invoices(cutoff_date, policy, db, dry_run))
            elif data_type == "feedback":
                results.update(self._process_feedback(cutoff_date, policy, db, dry_run))
            elif data_type == "user":
                results.update(self._process_users(cutoff_date, policy, db, dry_run))
            else:
                return {
                    "success": False,
                    "error": f"Unknown data type: {data_type}"
                }
            
            results["success"] = True
            return results
        except Exception as e:
            logger.error(f"Failed to apply retention policy for {data_type}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_bookings(self, cutoff_date: datetime, policy: RetentionPolicy, db: Session, dry_run: bool) -> Dict[str, Any]:
        """Process old bookings"""
        old_bookings = db.query(Booking).filter(
            Booking.created_at < cutoff_date
        ).all()
        
        count = 0
        for booking in old_bookings:
            if not dry_run:
                if policy.action == "anonymize":
                    booking.user_email = f"anonymized_{booking.id}@anonymized.local"
                    booking.notes = None
                elif policy.action == "delete":
                    db.delete(booking)
            count += 1
        
        if not dry_run:
            db.commit()
        
        return {"processed_count": count}
    
    def _process_payments(self, cutoff_date: datetime, policy: RetentionPolicy, db: Session, dry_run: bool) -> Dict[str, Any]:
        """Process old payments"""
        old_payments = db.query(Payment).filter(
            Payment.created_at < cutoff_date
        ).all()
        
        count = 0
        for payment in old_payments:
            if not dry_run:
                if policy.action == "anonymize":
                    payment.transaction_id = f"anonymized_{payment.id}"
                    payment.metadata = None
                elif policy.action == "delete":
                    db.delete(payment)
            count += 1
        
        if not dry_run:
            db.commit()
        
        return {"processed_count": count}
    
    def _process_invoices(self, cutoff_date: datetime, policy: RetentionPolicy, db: Session, dry_run: bool) -> Dict[str, Any]:
        """Process old invoices"""
        old_invoices = db.query(Invoice).filter(
            Invoice.created_at < cutoff_date
        ).all()
        
        count = 0
        for invoice in old_invoices:
            if not dry_run:
                if policy.action == "anonymize":
                    invoice.invoice_number = f"ANON_{invoice.id}"
                    invoice.notes = None
                elif policy.action == "delete":
                    db.delete(invoice)
            count += 1
        
        if not dry_run:
            db.commit()
        
        return {"processed_count": count}
    
    def _process_feedback(self, cutoff_date: datetime, policy: RetentionPolicy, db: Session, dry_run: bool) -> Dict[str, Any]:
        """Process old feedback"""
        old_feedback = db.query(Feedback).filter(
            Feedback.created_at < cutoff_date
        ).all()
        
        count = 0
        for feedback in old_feedback:
            if not dry_run:
                if policy.action == "anonymize":
                    feedback.user_email = f"anonymized_{feedback.id}@anonymized.local"
                    feedback.message = "[Content anonymized]"
                elif policy.action == "delete":
                    db.delete(feedback)
            count += 1
        
        if not dry_run:
            db.commit()
        
        return {"processed_count": count}
    
    def _process_users(self, cutoff_date: datetime, policy: RetentionPolicy, db: Session, dry_run: bool) -> Dict[str, Any]:
        """Process inactive users"""
        # Only process users who haven't logged in for the retention period
        old_users = db.query(User).filter(
            and_(
                User.last_login < cutoff_date,
                User.is_active == False
            )
        ).all()
        
        count = 0
        for user in old_users:
            if not dry_run:
                if policy.action == "anonymize":
                    user.email = f"anonymized_{user.id}@anonymized.local"
                    user.username = f"anonymized_user_{user.id}"
                    user.full_name = "Anonymized User"
                    user.phone_number = None
                    user.avatar_url = None
                elif policy.action == "delete":
                    # Use compliance service for proper deletion
                    self.compliance_service.delete_user_data(user.id, db, anonymize=True)
            count += 1
        
        if not dry_run:
            db.commit()
        
        return {"processed_count": count}
    
    def apply_all_policies(self, db: Session, dry_run: bool = False) -> Dict[str, Any]:
        """Apply all retention policies"""
        results = {
            "success": True,
            "policies_applied": [],
            "total_processed": 0,
            "dry_run": dry_run,
            "applied_at": datetime.utcnow().isoformat()
        }
        
        for data_type in self.policies.keys():
            policy_result = self.apply_retention_policy(data_type, db, dry_run)
            results["policies_applied"].append(policy_result)
            if policy_result.get("success"):
                results["total_processed"] += policy_result.get("processed_count", 0)
        
        return results

