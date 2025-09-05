# Import all models to ensure they're registered with SQLAlchemy
from .sessions import CodeSession, TerminalCommand
from .users import User  
from .submissions import CodeSubmission

__all__ = [
    "CodeSession",
    "TerminalCommand", 
    "User",
    "CodeSubmission"
]