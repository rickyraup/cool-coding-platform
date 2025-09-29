"""PostgreSQL database configuration and connection management."""

import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Optional
from urllib.parse import unquote

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Database configuration - Supabase only
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    msg = "DATABASE_URL environment variable is required"
    raise Exception(msg)


class PostgreSQLDatabase:
    """PostgreSQL database manager with connection pooling."""

    def __init__(self) -> None:
        self.connection_params = self._parse_database_url()

    def _parse_database_url(self) -> dict[str, Any]:
        """Parse DATABASE_URL into connection parameters."""
        if DATABASE_URL.startswith("postgresql://"):
            # Remove postgresql:// prefix
            url = DATABASE_URL[13:]

            # Find the last @ to split auth from host (in case password has @)
            at_pos = url.rfind("@")
            if at_pos != -1:
                auth = url[:at_pos]
                host_db = url[at_pos + 1 :]

                # Split user:password (password might contain special chars)
                colon_pos = auth.find(":")
                if colon_pos != -1:
                    user = auth[:colon_pos]
                    password = auth[colon_pos + 1 :]
                else:
                    user = auth
                    password = None
            else:
                user = password = None
                host_db = url

            # Split host:port/database
            if "/" in host_db:
                host_port, database = host_db.split("/", 1)
            else:
                host_port = host_db
                database = "postgres"

            # Split host:port
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = int(port)
            else:
                host = host_port
                port = 5432

            return {
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": unquote(password) if password else None,
            }
        msg = f"Unsupported DATABASE_URL format: {DATABASE_URL}"
        raise ValueError(msg)

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a database connection with automatic cleanup."""
        connection = None
        try:
            connection = psycopg2.connect(**self.connection_params)
            connection.autocommit = False
            yield connection
        except Exception:
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                connection.close()

    @contextmanager
    def get_cursor(
        self,
        connection: psycopg2.extensions.connection,
    ) -> Generator[psycopg2.extras.DictCursor, None, None]:
        """Get a cursor with automatic cleanup."""
        cursor = None
        try:
            cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
            yield cursor
        except Exception:
            raise
        finally:
            if cursor:
                cursor.close()

    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> list[dict[str, Any]]:
        """Execute a SELECT query and return results."""
        with self.get_connection() as conn, self.get_cursor(conn) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_one(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> Optional[dict[str, Any]]:
        """Execute a SELECT query and return the first result."""
        with self.get_connection() as conn, self.get_cursor(conn) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None

    def execute_insert(
        self,
        query: str,
        params: Optional[tuple] = None,
    ) -> Optional[int]:
        """Execute an INSERT query and return the new ID."""
        with self.get_connection() as conn, self.get_cursor(conn) as cursor:
            cursor.execute(query + " RETURNING id", params)
            result = cursor.fetchone()
            conn.commit()
            return result["id"] if result else None

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an UPDATE/DELETE query and return affected rows count."""
        with self.get_connection() as conn, self.get_cursor(conn) as cursor:
            cursor.execute(query, params)
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows

    def execute_raw(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a raw SQL statement (for migrations, DDL, etc.)."""
        with self.get_connection() as conn:
            # Use regular cursor for DDL operations (not DictCursor)
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.execute("SELECT NOW()")
                    result = cursor.fetchone()
                    print(
                        f"✅ PostgreSQL connection successful! Current time: {result[0]}",
                    )
                    return True
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            return False


# Create global database instance
db = PostgreSQLDatabase()


def init_db() -> None:
    """Initialize the database connection and test it."""
    print("🗄️ Initializing PostgreSQL database connection...")

    if db.test_connection():
        print("✅ Database connection ready")
    else:
        print("❌ Database connection failed")
        msg = "Could not connect to PostgreSQL database"
        raise Exception(msg)


def get_db() -> PostgreSQLDatabase:
    """Get the database instance."""
    return db
