"""
Comprehensive Database Management Utilities

This module provides utilities for:
- Database initialization
- Backup and restore
- Health checks
- Migration management
- Database statistics
"""
import os
import subprocess
import json
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import logging

from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from database import engine, SessionLocal, check_database_connection, get_database_info
from models import Base, Tour, Booking, Payment

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Comprehensive database management class"""

    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)

    def initialize_database(self, drop_existing: bool = False) -> Dict[str, any]:
        """
        Initialize the database by creating all tables.
        
        Args:
            drop_existing: If True, drop all existing tables first
            
        Returns:
            Dictionary with initialization results
        """
        try:
            if drop_existing:
                logger.warning("Dropping all existing tables...")
                Base.metadata.drop_all(bind=engine)
            
            logger.info("Creating all database tables...")
            Base.metadata.create_all(bind=engine)
            
            return {
                "success": True,
                "message": "Database initialized successfully",
                "tables_created": list(Base.metadata.tables.keys())
            }
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return {
                "success": False,
                "message": f"Database initialization failed: {str(e)}"
            }

    def get_table_stats(self) -> Dict[str, any]:
        """
        Get statistics about all tables in the database.
        
        Returns:
            Dictionary with table statistics
        """
        stats = {}
        try:
            with SessionLocal() as db:
                # Get table names
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
                for table_name in tables:
                    try:
                        # Get row count
                        result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = result.scalar()
                        
                        # Get table size (PostgreSQL only)
                        if os.getenv("DATABASE_URL", "").startswith("postgresql"):
                            result = db.execute(
                                text(f"""
                                    SELECT 
                                        pg_size_pretty(pg_total_relation_size('{table_name}')) as size,
                                        pg_total_relation_size('{table_name}') as size_bytes
                                    FROM {table_name}
                                    LIMIT 1
                                """)
                            )
                            size_info = result.fetchone()
                            size = size_info[0] if size_info else "N/A"
                            size_bytes = size_info[1] if size_info else 0
                        else:
                            size = "N/A"
                            size_bytes = 0
                        
                        stats[table_name] = {
                            "row_count": row_count,
                            "size": size,
                            "size_bytes": size_bytes
                        }
                    except Exception as e:
                        logger.warning(f"Could not get stats for table {table_name}: {e}")
                        stats[table_name] = {"error": str(e)}
                
                return {
                    "success": True,
                    "tables": stats,
                    "total_tables": len(tables)
                }
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
            return {
                "success": False,
                "message": f"Failed to get table stats: {str(e)}"
            }

    def backup_database(self, backup_name: Optional[str] = None) -> Dict[str, any]:
        """
        Backup PostgreSQL database using pg_dump.
        
        Args:
            backup_name: Optional custom name for the backup file
            
        Returns:
            Dictionary with backup results
        """
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url.startswith("postgresql"):
            return {
                "success": False,
                "message": "Backup is only supported for PostgreSQL databases"
            }
        
        try:
            # Parse database URL
            # Format: postgresql://user:password@host:port/database
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            
            db_name = parsed.path.lstrip('/')
            db_user = parsed.username or "postgres"
            db_host = parsed.hostname or "localhost"
            db_port = parsed.port or 5432
            db_password = parsed.password
            
            # Generate backup filename
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{db_name}_{timestamp}.sql"
            
            backup_path = self.backup_dir / backup_name
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password
            
            # Run pg_dump
            cmd = [
                "pg_dump",
                "-h", db_host,
                "-p", str(db_port),
                "-U", db_user,
                "-d", db_name,
                "-F", "c",  # Custom format
                "-f", str(backup_path)
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                file_size = backup_path.stat().st_size
                return {
                    "success": True,
                    "message": "Database backup created successfully",
                    "backup_path": str(backup_path),
                    "backup_name": backup_name,
                    "file_size": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            else:
                return {
                    "success": False,
                    "message": f"Backup failed: {result.stderr}",
                    "error": result.stderr
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": "pg_dump not found. Please install PostgreSQL client tools."
            }
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "success": False,
                "message": f"Backup failed: {str(e)}"
            }

    def restore_database(self, backup_path: str, drop_existing: bool = False) -> Dict[str, any]:
        """
        Restore PostgreSQL database from backup.
        
        Args:
            backup_path: Path to the backup file
            drop_existing: If True, drop existing database objects first
            
        Returns:
            Dictionary with restore results
        """
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url.startswith("postgresql"):
            return {
                "success": False,
                "message": "Restore is only supported for PostgreSQL databases"
            }
        
        try:
            # Parse database URL
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            
            db_name = parsed.path.lstrip('/')
            db_user = parsed.username or "postgres"
            db_host = parsed.hostname or "localhost"
            db_port = parsed.port or 5432
            db_password = parsed.password
            
            backup_file = Path(backup_path)
            if not backup_file.exists():
                return {
                    "success": False,
                    "message": f"Backup file not found: {backup_path}"
                }
            
            # Set PGPASSWORD environment variable
            env = os.environ.copy()
            if db_password:
                env["PGPASSWORD"] = db_password
            
            # Run pg_restore
            cmd = [
                "pg_restore",
                "-h", db_host,
                "-p", str(db_port),
                "-U", db_user,
                "-d", db_name,
                "-c" if drop_existing else "",
                str(backup_file)
            ]
            cmd = [c for c in cmd if c]  # Remove empty strings
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Database restored successfully",
                    "backup_path": backup_path
                }
            else:
                return {
                    "success": False,
                    "message": f"Restore failed: {result.stderr}",
                    "error": result.stderr
                }
        except FileNotFoundError:
            return {
                "success": False,
                "message": "pg_restore not found. Please install PostgreSQL client tools."
            }
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return {
                "success": False,
                "message": f"Restore failed: {str(e)}"
            }

    def list_backups(self) -> List[Dict[str, any]]:
        """
        List all available database backups.
        
        Returns:
            List of backup information dictionaries
        """
        backups = []
        try:
            for backup_file in self.backup_dir.glob("*.sql"):
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            return backups
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []

    def optimize_database(self) -> Dict[str, any]:
        """
        Optimize PostgreSQL database (VACUUM and ANALYZE).
        
        Returns:
            Dictionary with optimization results
        """
        database_url = os.getenv("DATABASE_URL", "")
        
        if not database_url.startswith("postgresql"):
            return {
                "success": False,
                "message": "Optimization is only supported for PostgreSQL databases"
            }
        
        try:
            with SessionLocal() as db:
                # Run VACUUM ANALYZE
                db.execute(text("VACUUM ANALYZE"))
                db.commit()
                
                return {
                    "success": True,
                    "message": "Database optimization completed successfully"
                }
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return {
                "success": False,
                "message": f"Database optimization failed: {str(e)}"
            }

    def get_connection_pool_stats(self) -> Dict[str, any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        try:
            pool = engine.pool
            return {
                "success": True,
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get pool stats: {str(e)}"
            }

    def health_check(self) -> Dict[str, any]:
        """
        Perform comprehensive database health check.
        
        Returns:
            Dictionary with health check results
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "connection": check_database_connection(),
            "database_info": get_database_info(),
            "pool_stats": self.get_connection_pool_stats(),
            "table_stats": self.get_table_stats()
        }
        
        # Overall health status
        results["healthy"] = (
            results["connection"] and
            results["database_info"].get("status") == "connected"
        )
        
        return results


# Convenience functions
def init_db(drop_existing: bool = False):
    """Initialize database (convenience function)"""
    manager = DatabaseManager()
    return manager.initialize_database(drop_existing)


def backup_db(backup_name: Optional[str] = None):
    """Backup database (convenience function)"""
    manager = DatabaseManager()
    return manager.backup_database(backup_name)


def restore_db(backup_path: str, drop_existing: bool = False):
    """Restore database (convenience function)"""
    manager = DatabaseManager()
    return manager.restore_database(backup_path, drop_existing)


def health_check_db():
    """Health check database (convenience function)"""
    manager = DatabaseManager()
    return manager.health_check()

