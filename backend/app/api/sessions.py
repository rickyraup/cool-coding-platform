import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sessions import CodeSession
from app.schemas.sessions import (
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.core.session_manager import session_manager


router = APIRouter()

@router.get("/", response_model=SessionListResponse)
async def get_sessions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Get all coding sessions"""
    sessions = db.query(CodeSession).offset(skip).limit(limit).all()

    return SessionListResponse(
        success=True,
        data=sessions,
        message=f"Retrieved {len(sessions)} sessions",
    )

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db),
):
    """Create a new coding session"""
    session_id = str(uuid.uuid4())

    db_session = CodeSession(
        id=session_id,
        user_id=session_data.user_id or "anonymous",
        code=session_data.code or "# Write your Python code here\\nprint('Hello, World!')",
        language=session_data.language or "python",
        is_active=True,
    )

    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    return SessionResponse(
        success=True,
        data=db_session,
        message="Session created successfully",
    )

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific coding session"""
    db_session = db.query(CodeSession).filter(CodeSession.id == session_id).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found",
        )

    return SessionResponse(
        success=True,
        data=db_session,
        message="Session retrieved successfully",
    )

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    db: Session = Depends(get_db),
):
    """Update a coding session"""
    db_session = db.query(CodeSession).filter(CodeSession.id == session_id).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found",
        )

    # Update fields
    update_data = session_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_session, field, value)

    db_session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_session)

    return SessionResponse(
        success=True,
        data=db_session,
        message="Session updated successfully",
    )

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete a coding session"""
    db_session = db.query(CodeSession).filter(CodeSession.id == session_id).first()

    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with id {session_id} not found",
        )

    db.delete(db_session)
    db.commit()

    return {
        "success": True,
        "message": "Session deleted successfully",
    }

@router.get("/terminal/active")
async def get_active_terminal_sessions():
    """Get all active terminal sessions (process isolation)"""
    sessions = session_manager.list_sessions()
    
    return {
        "success": True,
        "data": sessions,
        "count": len(sessions),
        "message": f"Retrieved {len(sessions)} active terminal sessions",
    }

@router.get("/terminal/{session_id}")
async def get_terminal_session_info(session_id: str):
    """Get information about a specific terminal session"""
    session_info = session_manager.get_session_info(session_id)
    
    if not session_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terminal session with id {session_id} not found",
        )
    
    return {
        "success": True,
        "data": session_info,
        "message": "Terminal session info retrieved successfully",
    }

@router.delete("/terminal/{session_id}")
async def cleanup_terminal_session(session_id: str):
    """Clean up a specific terminal session"""
    success = await session_manager.cleanup_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Terminal session with id {session_id} not found",
        )
    
    return {
        "success": True,
        "message": f"Terminal session {session_id} cleaned up successfully",
    }
