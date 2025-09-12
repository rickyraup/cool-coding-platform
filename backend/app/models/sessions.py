from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CodeSession(Base):
    __tablename__ = "code_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, default="anonymous", index=True)
    code = Column(
        Text, default="# Write your Python code here\\nprint('Hello, World!')",
    )
    language = Column(String, default="python")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )
    is_active = Column(Boolean, default=True)


class TerminalCommand(Base):
    __tablename__ = "terminal_commands"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("code_sessions.id"), index=True)
    command = Column(Text, nullable=False)
    output = Column(Text, default="")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    exit_code = Column(Integer, nullable=True)

    # Relationship
    session = relationship("CodeSession")
