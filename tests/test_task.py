import pytest
from tasks.task import Task

def test_task_create(connection):
    """Test creating a new task."""
    # Test with just task text
    task_id = Task.create(connection, "Test create task")
    assert task_id is not None

    # Test with task text and URL
    task_id_with_url = Task.create(connection, "Test create task with URL", "https://example.com")
    assert task_id_with_url is not None

    # Verify tasks were created
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    assert count == 2

def test_task_mark_done(sample_tasks, connection):
    """Test marking a task as done."""
    # Get first task
    cur = connection.cursor()
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Mark as done
    task.mark_done(connection)

    # Check it's marked done
    cur.execute("SELECT dt_completed FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result is not None
    assert result["dt_completed"] != 0  # Should be a timestamp

def test_task_update_details(sample_tasks, connection):
    """Test updating task details."""
    # Get first task
    cur = connection.cursor()
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Update just text
    new_text = "Updated task text"
    task.update_details(connection, new_text)

    # Verify update
    cur.execute("SELECT task, url FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result["task"] == new_text
    assert result["url"] == task.url  # Should be unchanged

    # Update text and URL
    new_url = "https://example.com/updated"
    task.update_details(connection, new_text, new_url)

    # Verify update
    cur.execute("SELECT task, url FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result["task"] == new_text
    assert result["url"] == new_url

def test_task_delete(sample_tasks, connection):
    """Test deleting a task."""
    # Get count before deletion
    cur = connection.cursor()
    cur.execute("SELECT COUNT(*) FROM tasks")
    count_before = cur.fetchone()[0]

    # Get first task
    cur.execute("SELECT * FROM tasks LIMIT 1")
    row = cur.fetchone()
    task = Task(**dict(row))

    # Delete task
    task.delete(connection)

    # Check it's deleted
    cur.execute("SELECT COUNT(*) FROM tasks")
    count_after = cur.fetchone()[0]
    assert count_after == count_before - 1

    # Check specific task is gone
    cur.execute("SELECT * FROM tasks WHERE id = ?", [task.id])
    result = cur.fetchone()
    assert result is None