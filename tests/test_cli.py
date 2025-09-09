import pytest
import sys
from io import StringIO
from unittest.mock import patch
import sqlite3

from tasks.main import main


@pytest.fixture
def capture_output():
    """Fixture to capture stdout/stderr"""
    output = StringIO()
    with patch("sys.stdout", output):
        yield output


def test_add_task(mock_env_db_path, monkeypatch):
    """Test adding a task via CLI."""
    # Mock the sys.argv to simulate CLI call
    test_args = ["tasks", "add", "Test CLI task"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    # Check output message indicates task was created
    assert "Created Task #" in output.getvalue()

    # Verify task was created in database
    conn = sqlite3.connect(mock_env_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT task FROM tasks WHERE task = ?", ["Test CLI task"])
    result = cur.fetchone()
    assert result is not None
    conn.close()


def test_show_tasks(mock_env_db_path, monkeypatch):
    """Test showing tasks."""
    # First add a task so we have something to show
    conn = sqlite3.connect(mock_env_db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (task) VALUES (?)", ["Task to display"])
    conn.commit()
    conn.close()

    # Mock CLI arguments for show command
    test_args = ["tasks", "show"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    # Verify output contains our task
    assert "Task to display" in output.getvalue()




# The following commands have been removed from CLI and are now TUI-only:
# - do (mark task as done)  
# - del (delete task)
# - priority up/down
# - mode/state setting
