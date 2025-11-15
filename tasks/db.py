from sqlite3 import Connection
from typing import Any, Dict, List, Optional

from .task import Task, parse_entry_text


class TaskDb:
    """Lightweight wrapper around a sqlite3 connection for task queries."""

    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def create_schema(self) -> None:
        """Create the minimal schema for tasks."""
        cur = self.conn.cursor()
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
        self.conn.commit()

    def get_task(self, task_id: int) -> Optional[Task]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", [task_id])
        row = cur.fetchone()
        if row:
            return Task(**dict(row))
        return None

    def get_tasks(self) -> List[Task]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 ORDER BY priority, id")
        rows = cur.fetchall()
        return [Task(**dict(row)) for row in rows]

    def get_tasks_new(self, days: int) -> List[Task]:
        cur = self.conn.cursor()
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed = 0
               AND dt_created >= date('now', '-{days} days')
             ORDER BY priority, id
        """
        cur.execute(sql)
        rows = cur.fetchall()
        return [Task(**dict(row)) for row in rows]

    def get_tasks_com(self, days: int) -> List[Task]:
        cur = self.conn.cursor()
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed >= date('now', '-{days} days')
        """
        cur.execute(sql)
        rows = cur.fetchall()
        return [Task(**dict(row)) for row in rows]

    def increase_priority(self, task_id: int) -> None:
        """Increase task priority (decrease number)."""
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE tasks
               SET priority = MAX(0, priority - 1)
             WHERE id = ?
            """,
            [task_id],
        )
        self.conn.commit()

    def decrease_priority(self, task_id: int) -> None:
        """Decrease task priority (increase number)."""
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE tasks
               SET priority = MIN(4, priority + 1)
             WHERE id = ?
            """,
            [task_id],
        )
        self.conn.commit()

    def set_task_state(self, task_id: int, state: str) -> None:
        """Set task state to one of: Now, Backlog, Done, Archive."""
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE tasks
               SET state = ?
             WHERE id = ?
            """,
            [state, task_id],
        )
        self.conn.commit()

    def get_tasks_by_state(self, state: str) -> List[Task]:
        """Get all tasks for a specific state."""
        cur = self.conn.cursor()
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

    def create_task(self, args: dict) -> Optional[int]:
        """Create a new task using CLI args and return the inserted id."""
        entry_text = args["task_entry"]
        title_text, url = parse_entry_text(entry_text)

        columns = ["title", "url"]
        values = [title_text, url]

        priority = args.get("priority")
        if priority is not None:
            columns.append("priority")
            values.append(priority)

        state = args.get("state")
        if state:
            columns.append("state")
            values.append(state)

        placeholders = ", ".join(["?"] * len(values))
        sql = f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({placeholders})"

        cur = self.conn.cursor()
        try:
            cur.execute(sql, values)
            self.conn.commit()
            return cur.lastrowid
        except Exception:
            self.conn.rollback()
            return None

    def mark_task_done(self, task_id: int) -> bool:
        """Mark the specified task as completed."""
        cur = self.conn.cursor()
        sql = """
            UPDATE tasks
               SET dt_completed = CURRENT_TIMESTAMP
             WHERE id = ?
        """
        try:
            cur.execute(sql, [task_id])
            self.conn.commit()
            return cur.rowcount > 0
        except Exception:
            self.conn.rollback()
            return False

    def update_task(self, task_id: int, updates: Dict[str, Optional[Any]]) -> bool:
        """Update arbitrary fields on a task."""
        if not updates:
            return True

        assignments = ", ".join(f"{field} = ?" for field in updates.keys())
        values = list(updates.values()) + [task_id]

        cur = self.conn.cursor()
        try:
            cur.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", values)
            self.conn.commit()
            return cur.rowcount > 0
        except Exception:
            self.conn.rollback()
            return False

    def delete_task(self, task_id: int) -> bool:
        """Delete a task from the database."""
        cur = self.conn.cursor()
        try:
            cur.execute("DELETE FROM tasks WHERE id = ?", [task_id])
            self.conn.commit()
            return cur.rowcount > 0
        except Exception:
            self.conn.rollback()
            return False
