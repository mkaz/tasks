from sqlite3 import Connection
from typing import List, Optional

from tasks.task import Task


def create_schema(conn: Connection) -> None:
    """Create the minimal schema for tasks."""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            notes TEXT,
            priority INTEGER DEFAULT 2,
            state TEXT DEFAULT 'Backlog',
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def get_task(conn: Connection, task_id: int) -> Optional[Task]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", [task_id])
    row = cur.fetchone()
    if row:
        return Task(**dict(row))
    return None


def get_tasks(conn: Connection) -> List[Task]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 ORDER BY priority, id")
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def get_tasks_new(conn: Connection, days: int) -> List[Task]:
    cur = conn.cursor()
    sql = f"""
        SELECT * FROM tasks
         WHERE dt_completed = 0
           AND dt_created >= date('now', '-{days} days')
         ORDER BY priority, id
    """
    cur.execute(sql)
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def get_tasks_com(conn: Connection, days: int) -> List[Task]:
    cur = conn.cursor()
    sql = f"""
        SELECT * FROM tasks
         WHERE dt_completed >= date('now', '-{days} days')
    """
    cur.execute(sql)
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def increase_priority(conn: Connection, task_id: int) -> None:
    """Increase task priority (decrease number)."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tasks
           SET priority = MAX(0, priority - 1)
         WHERE id = ?
        """,
        [task_id],
    )
    conn.commit()


def decrease_priority(conn: Connection, task_id: int) -> None:
    """Decrease task priority (increase number)."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tasks
           SET priority = MIN(4, priority + 1)
         WHERE id = ?
        """,
        [task_id],
    )
    conn.commit()


def set_task_state(conn: Connection, task_id: int, state: str) -> None:
    """Set task state to one of: Now, Backlog, Done, Archive."""
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tasks
           SET state = ?
         WHERE id = ?
        """,
        [state, task_id],
    )
    conn.commit()


def get_tasks_by_state(conn: Connection, state: str) -> List[Task]:
    """Get all tasks for a specific state."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM tasks
         WHERE dt_completed = 0
           AND state = ?
         ORDER BY priority, id
        """,
        [state],
    )
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]
