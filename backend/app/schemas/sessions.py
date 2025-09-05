from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionBase(BaseModel):
    user_id: Optional[str] = "anonymous"
    code: Optional[str] = "# Write your Python code here\\nprint('Hello, World!')"
    language: Optional[str] = "python"
    is_active: Optional[bool] = True

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    code: Optional[str] = None
    is_active: Optional[bool] = None

class SessionData(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    success: bool
    data: SessionData
    message: str

class SessionListResponse(BaseModel):
    success: bool
    data: List[SessionData]
    message: str