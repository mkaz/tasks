import sqlite3
import pytest
from tasks.db import TaskDb

def test_create_schema(temp_db):
    """Test creating the schema."""
    # Schema should already be created by the fixture
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row

    # Check if the table exists
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    assert cur.fetchone() is not None

    # Check that calling create_schema again doesn't error
    TaskDb(conn).create_schema()
    conn.close()

def test_get_task(sample_tasks):
    """Test getting a single task."""
    # Get the ID of a task we know exists
    cur = sample_tasks.cursor()
    cur.execute("SELECT id FROM tasks LIMIT 1")
    task_id = cur.fetchone()[0]

    # Get the task
    db = TaskDb(sample_tasks)

    task = db.get_task(task_id)
    assert task is not None
    assert task.id == task_id

    # Try to get a task that doesn't exist
    nonexistent_task = db.get_task(9999)
    assert nonexistent_task is None

def test_get_tasks(sample_tasks):
    """Test getting all active tasks."""
    # First, make sure none are marked complete
    cur = sample_tasks.cursor()
    cur.execute("UPDATE tasks SET dt_completed = 0")
    sample_tasks.commit()

    # Get all tasks
    db = TaskDb(sample_tasks)
    tasks = db.get_tasks()

    # Should be the same number we added in the fixture
    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]
    assert len(tasks) == count

    # Mark one as done
    cur.execute("UPDATE tasks SET dt_completed = CURRENT_TIMESTAMP WHERE id = (SELECT id FROM tasks LIMIT 1)")
    sample_tasks.commit()

    # Get active tasks
    active_tasks = db.get_tasks()
    assert len(active_tasks) == count - 1

def test_increase_priority(sample_tasks):
    """Test increasing a task's priority."""
    # Get a task
    cur = sample_tasks.cursor()
    cur.execute("SELECT id, priority FROM tasks LIMIT 1")
    row = cur.fetchone()
    task_id, old_priority = row["id"], row["priority"]

    # Increase priority
    db = TaskDb(sample_tasks)
    db.adjust_priority(task_id, increase=True)

    # Check priority was increased
    cur.execute("SELECT priority FROM tasks WHERE id = ?", [task_id])
    new_priority = cur.fetchone()["priority"]

    # Lower number = higher priority
    assert new_priority == max(0, old_priority - 1)

    # Test boundary condition - priority 0
    cur.execute("UPDATE tasks SET priority = 0 WHERE id = ?", [task_id])
    sample_tasks.commit()

    db.adjust_priority(task_id, increase=True)

    cur.execute("SELECT priority FROM tasks WHERE id = ?", [task_id])
    boundary_priority = cur.fetchone()["priority"]
    assert boundary_priority == 0  # Can't go below 0

def test_decrease_priority(sample_tasks):
    """Test decreasing a task's priority."""
    # Get a task
    cur = sample_tasks.cursor()
    cur.execute("SELECT id, priority FROM tasks LIMIT 1")
    row = cur.fetchone()
    task_id, old_priority = row["id"], row["priority"]

    # Decrease priority
    db = TaskDb(sample_tasks)
    db.adjust_priority(task_id, increase=False)

    # Check priority was decreased
    cur.execute("SELECT priority FROM tasks WHERE id = ?", [task_id])
    new_priority = cur.fetchone()["priority"]

    # Higher number = lower priority
    assert new_priority == min(4, old_priority + 1)

    # Test boundary condition - priority 4
    cur.execute("UPDATE tasks SET priority = 4 WHERE id = ?", [task_id])
    sample_tasks.commit()

    db.adjust_priority(task_id, increase=False)

    cur.execute("SELECT priority FROM tasks WHERE id = ?", [task_id])
    boundary_priority = cur.fetchone()["priority"]
    assert boundary_priority == 4  # Can't go above 4

def test_set_task_state(sample_tasks):
    """Test setting a task's state."""
    # Get a task
    cur = sample_tasks.cursor()
    cur.execute("SELECT id FROM tasks LIMIT 1")
    task_id = cur.fetchone()["id"]

    # Set to Now state
    db = TaskDb(sample_tasks)
    db.set_task_state(task_id, "Now")

    # Check state was set
    cur.execute("SELECT state FROM tasks WHERE id = ?", [task_id])
    assert cur.fetchone()["state"] == "Now"

    # Set to Later state
    db.set_task_state(task_id, "Later")

    # Check state was set
    cur.execute("SELECT state FROM tasks WHERE id = ?", [task_id])
    assert cur.fetchone()["state"] == "Later"