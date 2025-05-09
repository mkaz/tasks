import pytest
import sqlite3
from pathlib import Path
import tempfile
import os
from tasks.dbactions import create_schema


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file that will be used as the SQLite DB
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Connect to the DB and create the schema
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    create_schema(conn)  # Use the application's schema creation function
    conn.close()

    # Return the path to the temporary DB
    yield path

    # Clean up - remove the temporary file
    Path(path).unlink()


@pytest.fixture
def mock_env_db_path(monkeypatch, temp_db):
    """Set the TASKS_DB environment variable to point to our temp db."""
    monkeypatch.setenv("TASKS_DB", temp_db)
    return temp_db


@pytest.fixture
def connection(temp_db):
    """Get a connection to the test database."""
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def sample_tasks(connection):
    """Add some sample tasks to the test database."""
    cur = connection.cursor()
    sample_data = [
        ("Test task 1", None, 2, "Now"),
        ("Test task 2", "https://example.com", 1, "Later"),
        ("Test task 3", None, 3, "Now"),
    ]

    for task, url, priority, mode in sample_data:
        cur.execute(
            "INSERT INTO tasks (task, url, priority, mode) VALUES (?, ?, ?, ?)",
            (task, url, priority, mode),
        )

    connection.commit()
    return connection
