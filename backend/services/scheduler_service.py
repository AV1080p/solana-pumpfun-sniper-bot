"""
Scheduled Task Service

Runs automated tasks for data retention policies and backups.
Uses the schedule library for periodic task execution.
"""
import schedule
import time
import logging
import threading
from datetime import datetime
from typing import Optional

from database import SessionLocal
from services.retention_service import RetentionService

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for running scheduled tasks"""
    
    def __init__(self):
        self.retention_service = RetentionService()
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def setup_retention_schedule(self):
        """Setup scheduled retention policy execution"""
        # Run retention policies daily at 2 AM
        schedule.every().day.at("02:00").do(self._run_retention_policies)
        logger.info("Retention policy scheduler configured (daily at 2:00 AM)")
    
    def _run_retention_policies(self):
        """Run all retention policies"""
        try:
            logger.info("Starting scheduled retention policy execution")
            db = SessionLocal()
            try:
                result = self.retention_service.apply_all_policies(db, dry_run=False)
                if result.get("success"):
                    logger.info(f"Retention policies applied successfully. Processed {result.get('total_processed', 0)} records")
                else:
                    logger.error(f"Retention policy execution failed: {result.get('error')}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error running retention policies: {e}")
    
    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.setup_retention_schedule()
        self.running = True
        
        def run_scheduler():
            logger.info("Scheduler service started")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            logger.info("Scheduler service stopped")
        
        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler thread started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        logger.info("Scheduler service stopped")
    
    def run_now(self, task_name: str = "retention"):
        """Run a scheduled task immediately"""
        if task_name == "retention":
            self._run_retention_policies()
        else:
            logger.warning(f"Unknown task: {task_name}")


# Singleton instance
_scheduler_service: Optional[SchedulerService] = None


def get_scheduler_service() -> SchedulerService:
    """Get or create scheduler service singleton"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service

