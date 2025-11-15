import pytest
from tasks.task import Task
from tasks.db import TaskDb


def test_task_create(connection):
    """Test creating a new task."""
    db = TaskDb(connection)
    # Test with just task text
    entry = {"task_entry": "Test create task"}
    task_id = db.create_task(entry)
    assert task_id is not None

    # Test with task text and URL
    entry = {"task_entry": "Test create task https://example.com"}
    task_id_with_url = db.create_task(entry)
    assert task_id_with_url is not None
    # add check for URL in db for this task
    cur = connection.cursor()
    cur.execute("SELECT url FROM tasks WHERE id = ?", [task_id_with_url])
    result = cur.fetchone()
    assert result[0] == "https://example.com"

    # Test with explicit priority and state
    entry = {"task_entry": "Task with flags", "priority": 0, "state": "Now"}
    task_id_with_flags = db.create_task(entry)
    assert task_id_with_flags is not None
    cur.execute("SELECT priority, state FROM tasks WHERE id = ?", [task_id_with_flags])
    result = cur.fetchone()
    assert result["priority"] == 0
    assert result["state"] == "Now"

    # Verify tasks were created
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    assert count == 3


def test_task_mark_done(sample_tasks, connection):
    """Test marking a task as done."""
    db = TaskDb(connection)
    # Get first task
    cur = connection.cursor()
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Mark as done
    db.mark_task_done(task.id)

    # Check it's marked done
    cur.execute("SELECT dt_completed FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result is not None
    assert result["dt_completed"] != 0  # Should be a timestamp


def test_task_update_details(sample_tasks, connection):
    """Test updating task details."""
    db = TaskDb(connection)
    # Get first task
    cur = connection.cursor()
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Update just text
    new_title = "Updated task text"
    assert db.update_task(task.id, {"title": new_title})

    # Verify update
    cur.execute("SELECT title, url FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result["title"] == new_title
    assert result["url"] == task.url  # Should be unchanged

    # Update text and URL
    new_url = "https://example.com/updated"
    assert db.update_task(task.id, {"title": new_title, "url": new_url})

    # Verify update
    cur.execute("SELECT title, url FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result["title"] == new_title
    assert result["url"] == new_url


def test_task_delete(sample_tasks, connection):
    """Test deleting a task."""
    db = TaskDb(connection)
    # Get count before deletion
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    count_before = cur.fetchone()[0]

    # Get first task
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Delete task
    assert db.delete_task(task.id)

    # Check it's deleted
    cur.execute("SELECT COUNT(*) FROM tasks")
    count_after = cur.fetchone()[0]
    assert count_after == count_before - 1

    # Check specific task is gone
    cur.execute("SELECT * FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result is None
