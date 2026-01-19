from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
import os
import logging
from dotenv import load_dotenv
from contextlib import contextmanager
from typing import Generator

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/tourist_db")

# PostgreSQL connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

# Create engine with connection pooling for PostgreSQL
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        poolclass=pool.QueuePool,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=True,  # Verify connections before using
        echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Log SQL queries
        connect_args={
            "connect_timeout": 10,
            "application_name": "tourist_app_backend"
        }
    )
    logger.info(f"PostgreSQL connection pool configured: size={POOL_SIZE}, max_overflow={MAX_OVERFLOW}")
elif DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool
    )
    logger.info("SQLite database configured")
else:
    raise ValueError(f"Unsupported database URL: {DATABASE_URL}")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Connection event listeners for PostgreSQL
@event.listens_for(Engine, "connect")
def set_postgres_pragmas(dbapi_conn, connection_record):
    """Set PostgreSQL connection parameters"""
    if DATABASE_URL.startswith("postgresql"):
        with dbapi_conn.cursor() as cursor:
            # Set timezone
            cursor.execute("SET timezone = 'UTC'")
            # Set statement timeout (optional)
            # cursor.execute("SET statement_timeout = '30s'")


@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout"""
    logger.debug("Connection checked out from pool")


@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection checkin"""
    logger.debug("Connection returned to pool")


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    Automatically handles session lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Context manager for database sessions
@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this for non-FastAPI contexts (scripts, background tasks, etc.)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    Check if database connection is healthy.
    Returns True if connection is successful, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection check: SUCCESS")
        return True
    except Exception as e:
        logger.error(f"Database connection check: FAILED - {e}")
        return False


def get_database_info() -> dict:
    """
    Get database connection information.
    Returns a dictionary with database stats.
    """
    try:
        with engine.connect() as conn:
            if DATABASE_URL.startswith("postgresql"):
                result = conn.execute("SELECT version()")
                version = result.scalar()
                result = conn.execute("SELECT current_database()")
                db_name = result.scalar()
                result = conn.execute("SELECT current_user")
                db_user = result.scalar()
                
                return {
                    "status": "connected",
                    "type": "PostgreSQL",
                    "version": version,
                    "database": db_name,
                    "user": db_user,
                    "pool_size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow()
                }
            else:
                return {
                    "status": "connected",
                    "type": "SQLite",
                    "database": DATABASE_URL.split("/")[-1]
                }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

