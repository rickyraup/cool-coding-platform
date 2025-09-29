"""Pytest configuration and fixtures for backend tests."""

import asyncio
import os
import tempfile
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.core.postgres import PostgreSQLDatabase, get_db
from app.main import app


class MockPostgreSQLDatabase:
    """Mock database for testing that simulates PostgreSQL operations."""

    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.reviews = {}
        self.next_id = 1

    def execute_insert(self, query: str, params: tuple) -> int:
        """Mock insert operation."""
        table_id = self.next_id
        self.next_id += 1

        if "users" in query:
            self.users[table_id] = {
                "id": table_id,
                "username": params[0],
                "email": params[1],
                "password_hash": params[2],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        elif "code_sessions" in query:
            self.sessions[table_id] = {
                "id": table_id,
                "uuid": params[0],
                "user_id": params[1],
                "name": params[2],
                "code": params[3] if len(params) > 3 else "",
                "language": params[4] if len(params) > 4 else "python",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }

        return table_id

    def execute_one(self, query: str, params: tuple):
        """Mock single result query."""
        if "users" in query and "WHERE id" in query:
            user_id = params[0]
            return self.users.get(user_id)
        elif "code_sessions" in query and "WHERE uuid" in query:
            uuid = params[0]
            for session in self.sessions.values():
                if session["uuid"] == uuid:
                    return session
        return None

    def execute_query(self, query: str, params: tuple = None):
        """Mock multi-result query."""
        if "users" in query:
            return list(self.users.values())
        elif "code_sessions" in query:
            return list(self.sessions.values())
        return []

    def execute_update(self, query: str, params: tuple) -> int:
        """Mock update operation."""
        return 1

    def test_connection(self) -> bool:
        """Mock connection test."""
        return True


@pytest.fixture(scope="function")
def test_db_session():
    """Create a test database session."""
    return MockPostgreSQLDatabase()


@pytest.fixture(scope="function")
def client(test_db_session) -> TestClient:
    """Create a test client with dependency overrides."""
    def override_get_db():
        return test_db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture(scope="function")
def sample_session_data() -> dict:
    """Sample session data for testing."""
    return {
        "user_id": 1,
        "name": "Test Session",
        "code": "print('Hello, World!')",
        "language": "python"
    }


@pytest.fixture(scope="function")
def sample_review_data() -> dict:
    """Sample review request data for testing."""
    return {
        "session_id": "test-session-uuid-123",
        "title": "Test Review Request",
        "description": "This is a test review request",
        "priority": "medium"
    }


@pytest_asyncio.fixture
async def async_client(test_db_session) -> AsyncGenerator[TestClient, None]:
    """Async test client for testing async endpoints."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()