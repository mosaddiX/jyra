"""
Pytest configuration for Jyra AI Roleplay Bot tests
"""

from jyra.db.init_db import init_db
from dotenv import load_dotenv
import os
import sys
import pytest
import asyncio
import sqlite3
import tempfile

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Import Jyra modules


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_path():
    """Create a temporary database for testing."""
    # Create a temporary file
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = db_file.name
    db_file.close()

    # Initialize the test database
    os.environ["DATABASE_PATH"] = db_path
    init_db()

    yield db_path

    # Clean up
    os.unlink(db_path)


@pytest.fixture(scope="session")
def test_db_connection(test_db_path):
    """Create a connection to the test database."""
    conn = sqlite3.connect(test_db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def test_db_cursor(test_db_connection):
    """Create a cursor for the test database."""
    cursor = test_db_connection.cursor()
    yield cursor
    test_db_connection.commit()
    cursor.close()


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration."""
    # Load environment variables
    load_dotenv()

    # Return test configuration
    return {
        "telegram_token": os.environ.get("TELEGRAM_BOT_TOKEN", "test_token"),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", "test_api_key"),
        "database_path": os.environ.get("DATABASE_PATH", ":memory:")
    }
