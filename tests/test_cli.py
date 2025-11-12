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


def test_default_command_shows_tasks(mock_env_db_path, monkeypatch):
    """Running without a subcommand should behave like `tasks show`."""
    conn = sqlite3.connect(mock_env_db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (task) VALUES (?)", ["Default Task"])
    conn.commit()
    conn.close()

    test_args = ["tasks"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    assert "Default Task" in output.getvalue()


def test_default_view_hides_done_tasks(mock_env_db_path, monkeypatch):
    """Completed tasks should not appear in the default listing."""
    conn = sqlite3.connect(mock_env_db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (task) VALUES (?)", ["Active Task"])
    cur.execute(
        "INSERT INTO tasks (task, dt_completed) VALUES (?, datetime('now'))",
        ["Finished Task"],
    )
    conn.commit()
    conn.close()

    test_args = ["tasks"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    rendered = output.getvalue()
    assert "Active Task" in rendered
    assert "Finished Task" not in rendered
