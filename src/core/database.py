"""
Database configuration and session management.

Uses SQLAlchemy for ORM and SQLite for persistence.
Provides session factory and base class for models.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from src.core.config import settings

# Create SQLAlchemy engine
# Use StaticPool for SQLite to avoid threading issues in tests
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """Dependency for getting database session in FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database (create all tables) and apply any missing column migrations."""
    Base.metadata.create_all(bind=engine)

    # Add extracted_text column to existing metadata tables that predate this column
    from sqlalchemy import text, inspect
    with engine.connect() as conn:
        inspector = inspect(engine)
        existing_cols = {col["name"] for col in inspector.get_columns("metadata")}
        if "extracted_text" not in existing_cols:
            conn.execute(text("ALTER TABLE metadata ADD COLUMN extracted_text TEXT"))
            conn.commit()
