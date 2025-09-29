"""Datetime utility functions."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Get current UTC datetime with timezone information."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Get current UTC datetime as ISO string."""
    return utc_now().isoformat()
