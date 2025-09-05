from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": psutil.boot_time(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0",
        "message": "FastAPI server is running"
    }

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with system information"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": psutil.boot_time(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0",
        "system": {
            "memory": {
                "used": round(memory.used / 1024 / 1024, 2),
                "total": round(memory.total / 1024 / 1024, 2),
                "percent": memory.percent,
                "unit": "MB"
            },
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "platform": os.name
        },
        "message": "Detailed FastAPI server health information"
    }