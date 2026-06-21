from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import inspect, text

from app.core.config import settings

# Create SQLAlchemy engine
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
elif settings.DATABASE_URL.startswith("mysql"):
    # MySQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        echo=settings.DEBUG
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db() -> Session:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    # Import all models here to ensure they are registered
    from app.models import user, course, assignment, essay, quiz, attendance, grade, forum, message, notification, resource, calendar_event, student_performance
    
    # Create all tables
    Base.metadata.create_all(bind=engine)

# def seed_db():
#     """Seed sample data if the database is empty."""
#     from app.models.user import User
#     db = SessionLocal()
#     try:
#         if db.query(User).count() == 0:
#             from app.seed_data import seed_database
#             seed_database()
#     except Exception as e:
#         print(f"Seed skipped (non-fatal): {e}")
#     finally:
#         db.close()