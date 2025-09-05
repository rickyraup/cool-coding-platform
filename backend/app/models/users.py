"""User model for the coding platform."""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model representing platform users."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="user")  # user, reviewer, admin
    created_at = Column(DateTime(timezone=True), server_default=func.now())
