"""Health check API endpoints."""

import os
from datetime import datetime, timezone
from typing import Any

import psutil
from fastapi import APIRouter

router = APIRouter()


def _get_base_health_info() -> dict[str, Any]:
    """Get base health information shared across endpoints."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": psutil.boot_time(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "version": "1.0.0",
    }


@router.get("/")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        **_get_base_health_info(),
        "message": "FastAPI server is running",
    }


@router.get("/detailed")
async def detailed_health_check() -> dict[str, Any]:
    """Detailed health check with system information."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)

    return {
        **_get_base_health_info(),
        "system": {
            "memory": {
                "used": round(memory.used / 1024 / 1024, 2),
                "total": round(memory.total / 1024 / 1024, 2),
                "percent": memory.percent,
                "unit": "MB",
            },
            "cpu": {
                "usage_percent": cpu_percent,
                "count": psutil.cpu_count(),
            },
            "platform": os.name,
        },
        "message": "Detailed FastAPI server health information",
    }
