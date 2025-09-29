"""Database configuration and connection management."""

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker


load_dotenv()

# Database configuration - PostgreSQL only
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    msg = "DATABASE_URL environment variable is required"
    raise Exception(msg)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    # Import models to ensure they're registered with Base
    from app.models import (  # noqa: F401
        CodeSession,
        CodeSubmission,
        TerminalCommand,
        User,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
