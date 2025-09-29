"""Test environment settings."""

import os
from pathlib import Path

# Test database URL (will be overridden by conftest.py for SQLite)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://testuser:testpass@localhost:5433/test_coolcoding"
)

# Ensure we're in test mode
os.environ["TESTING"] = "true"

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_DATA_DIR.mkdir(exist_ok=True)