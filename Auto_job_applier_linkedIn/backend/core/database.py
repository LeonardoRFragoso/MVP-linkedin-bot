"""
Database configuration and session management for LinkedIn Bot White Label MVP.
Supports PostgreSQL (production) and SQLite (development).
"""

import os
import logging
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Base class for all models
Base = declarative_base()

# Database URL from environment
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./data/linkedin_bot.db'
)

# Determine if using SQLite
IS_SQLITE = DATABASE_URL.startswith('sqlite')


def get_engine():
    """
    Create and configure the database engine.
    
    Returns:
        Engine: SQLAlchemy engine instance
    """
    connect_args = {}
    
    if IS_SQLITE:
        # SQLite specific settings
        connect_args = {"check_same_thread": False}
        engine = create_engine(
            DATABASE_URL,
            connect_args=connect_args,
            poolclass=StaticPool,
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    else:
        # PostgreSQL settings
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            echo=os.getenv('DEBUG', 'false').lower() == 'true'
        )
    
    return engine


# Create engine
engine = get_engine()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    
    Usage:
        with get_db_session() as db:
            db.query(User).all()
    
    Yields:
        Session: Database session
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


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Call this on application startup.
    """
    from . import models  # Import models to register them
    
    # Create data directory for SQLite
    if IS_SQLITE:
        import os
        from pathlib import Path
        db_path = DATABASE_URL.replace('sqlite:///', '')
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {DATABASE_URL}")


def drop_db() -> None:
    """
    Drop all tables. USE WITH CAUTION!
    """
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped!")


def check_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


# ============================================================================
# Database Utilities
# ============================================================================

class DatabaseManager:
    """
    High-level database management utilities.
    """
    
    @staticmethod
    def create_tables():
        """Create all tables defined in models."""
        init_db()
    
    @staticmethod
    def drop_tables():
        """Drop all tables. USE WITH CAUTION!"""
        drop_db()
    
    @staticmethod
    def reset_database():
        """Drop and recreate all tables. USE WITH CAUTION!"""
        drop_db()
        init_db()
    
    @staticmethod
    def health_check() -> dict:
        """
        Perform database health check.
        
        Returns:
            dict: Health check results
        """
        result = {
            "database_url": DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL,
            "is_sqlite": IS_SQLITE,
            "connected": False,
            "error": None
        }
        
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            result["connected"] = True
        except Exception as e:
            result["error"] = str(e)
        
        return result


if __name__ == "__main__":
    print("=" * 60)
    print("Database Configuration Test")
    print("=" * 60)
    
    print(f"\nDatabase URL: {DATABASE_URL}")
    print(f"Is SQLite: {IS_SQLITE}")
    
    health = DatabaseManager.health_check()
    print(f"\nHealth Check:")
    for key, value in health.items():
        print(f"  {key}: {value}")
    
    if health["connected"]:
        print("\n✅ Database connection successful!")
        
        # Initialize tables
        print("\nInitializing tables...")
        init_db()
        print("✅ Tables created!")
    else:
        print("\n❌ Database connection failed!")
