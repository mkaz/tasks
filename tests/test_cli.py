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
    cur.execute("SELECT title FROM tasks WHERE title = ?", ["Test CLI task"])
    result = cur.fetchone()
    assert result is not None
    conn.close()


def test_add_task_with_flags(mock_env_db_path, monkeypatch):
    """Test adding a task with explicit state and priority."""
    test_args = ["tasks", "add", "-s", "Now", "-p", "1", "Flag task"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    conn = sqlite3.connect(mock_env_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, priority, state FROM tasks WHERE title = ?", ["Flag task"])
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row["priority"] == 1
    assert row["state"] == "Now"


def test_edit_task(mock_env_db_path, monkeypatch):
    """Test editing a task interactively."""
    conn = sqlite3.connect(mock_env_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, priority, state, notes) VALUES (?, ?, ?, ?)", ["Original", 2, "Backlog", "Old note"])
    conn.commit()
    conn.close()

    responses = iter([
        "Updated Title",
        "https://example.com/new",
        "0",
        "Now",
        "Updated note",
        "y",
    ])

    def fake_prompt(message, **kwargs):
        return next(responses)

    monkeypatch.setattr("tasks.editor.prompt", fake_prompt)

    test_args = ["tasks", "edit", "1"]
    output = StringIO()
    with patch.object(sys, "argv", test_args), patch("sys.stdout", output):
        main(skip_local=True)

    conn = sqlite3.connect(mock_env_db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT title, priority, state, notes, url FROM tasks WHERE id = 1")
    row = cur.fetchone()
    conn.close()

    assert row["title"] == "Updated Title"
    assert row["priority"] == 0
    assert row["state"] == "Now"
    assert row["notes"] == "Updated note"
    assert row["url"] == "https://example.com/new"


def test_show_tasks(mock_env_db_path, monkeypatch):
    """Test showing tasks."""
    # First add a task so we have something to show
    conn = sqlite3.connect(mock_env_db_path)
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (?)", ["Task to display"])
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
    cur.execute("INSERT INTO tasks (title) VALUES (?)", ["Default Task"])
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
    cur.execute("INSERT INTO tasks (title) VALUES (?)", ["Active Task"])
    cur.execute(
        "INSERT INTO tasks (title, dt_completed) VALUES (?, datetime('now'))",
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
