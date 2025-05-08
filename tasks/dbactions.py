from sqlite3 import Connection, Error
from typing import List, Optional
import sys


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            url TEXT,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER DEFAULT 2,
            mode TEXT DEFAULT 'Now' CHECK(mode IN ('Now', 'Later'))
        )
        """
    )
    conn.commit()


def get_schema_version(conn: Connection) -> int:
    """Get the current schema version."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT version FROM schema_version")
        result = cur.fetchone()
        if result and result[0] is not None:
            return result[0]
    except Error:  # Catches all SQLite-related errors
        pass
    return 0


def get_task(conn: Connection, task_id: int) -> List:
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", [task_id])
    return cur.fetchone()


def get_tasks(conn: Connection) -> List:
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 ORDER BY priority, id")
    return cur.fetchall()


def get_tasks_new(conn: Connection, days: int) -> List:
    cur = conn.cursor()
    sql = f"""
        SELECT * FROM tasks
         WHERE dt_completed = 0
           AND dt_created >= date('now', '-{days} days')
         ORDER BY priority, id
    """
    cur.execute(sql)
    return cur.fetchall()


def get_tasks_com(conn: Connection, days: int) -> List:
    cur = conn.cursor()
    sql = f"""
        SELECT * FROM tasks
         WHERE dt_completed >= date('now', '-{days} days')
    """
    cur.execute(sql)
    return cur.fetchall()


def insert_task(conn: Connection, task: str) -> Optional[int]:
    """Insert task into database"""
    cur = conn.cursor()
    sql = "INSERT INTO tasks (task) VALUES (?)"
    cur.execute(sql, [task])
    conn.commit()

    return cur.lastrowid


def mark_done(conn: Connection, task_id: int):
    """Mark task id done"""
    cur = conn.cursor()
    sql = """
        UPDATE tasks
           SET dt_completed = CURRENT_TIMESTAMP
         WHERE id = ?
    """
    cur.execute(sql, [task_id])
    conn.commit()


def task_update(
    conn: Connection, task_id: int, task_text: str, url: Optional[str] = None
):
    """Update task with new text and optionally a new URL"""
    cur = conn.cursor()
    fields_to_update = {"task": task_text}
    if url is not None:
        fields_to_update["url"] = url

    set_clause = ", ".join([f"{key} = ?" for key in fields_to_update])
    values = list(fields_to_update.values()) + [task_id]

    sql = f"""
        UPDATE tasks
           SET {set_clause}
         WHERE id = ?
    """
    cur.execute(sql, values)
    conn.commit()


def task_delete(conn: Connection, task_id: int):
    """Mark task id done"""
    cur = conn.cursor()
    sql = """
        DELETE FROM tasks
         WHERE id = ?
    """
    cur.execute(sql, [task_id])
    conn.commit()


def increase_priority(conn: Connection, task_id: int):
    """Increase task priority (decrease number)"""
    cur = conn.cursor()
    sql = """
        UPDATE tasks
           SET priority = MAX(0, priority - 1)
         WHERE id = ?
    """
    cur.execute(sql, [task_id])
    conn.commit()


def decrease_priority(conn: Connection, task_id: int):
    """Decrease task priority (increase number)"""
    cur = conn.cursor()
    sql = """
        UPDATE tasks
           SET priority = MIN(4, priority + 1)
         WHERE id = ?
    """
    cur.execute(sql, [task_id])
    conn.commit()


def set_task_mode(conn: Connection, task_id: int, mode: str):
    """Set task mode to one of: Now, Develop, Tinker"""
    cur = conn.cursor()
    # LIMIT clause is not needed in UPDATE statement since WHERE id = ?
    # already ensures we only update one row (id is primary key)
    sql = """
        UPDATE tasks
           SET mode = ?
         WHERE id = ?
    """
    cur.execute(sql, [mode, task_id])
    conn.commit()


def get_tasks_by_mode(conn: Connection, mode: str) -> List:
    """Get all tasks for a specific mode"""
    cur = conn.cursor()
    sql = """
        SELECT * FROM tasks
        WHERE dt_completed = 0
            AND mode = ?
        ORDER BY priority, id
    """
    cur.execute(sql, [mode])
    return cur.fetchall()


def migrate_schema(conn: Connection) -> None:
    """Migrate database schema."""

    cur = conn.cursor()

    # Drop schema_version table - not needed anymore
    cur.execute("DROP TABLE IF EXISTS schema_version")
    conn.commit()

    # Get current columns
    cur.execute("PRAGMA table_info(tasks)")
    columns = cur.fetchall()

    has_mode = any(col[1] == "mode" for col in columns)

    # Add mode column with default value
    if not has_mode:
        print("Adding mode column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN mode TEXT DEFAULT 'Now'
        """)
        conn.commit()

    # Add url column
    has_url = any(col[1] == "url" for col in columns)
    if not has_url:
        print("Adding url column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN url TEXT
        """)
        conn.commit()
