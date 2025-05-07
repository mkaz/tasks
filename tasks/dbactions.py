from sqlite3 import Connection
import sqlite3
from typing import List, Optional


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY
        )
        """
    )
    # Initialize schema version if not already set
    cur.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (1)")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            url TEXT,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER DEFAULT 2,
            mode TEXT DEFAULT 'A' CHECK(mode IN ('A', 'B', 'C'))
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
    except sqlite3.Error:  # Catches all SQLite-related errors
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

def get_tasks_by_mode(conn: Connection, mode: str) -> List:
    cur = conn.cursor()
    sql = """
        SELECT * FROM tasks
        WHERE dt_completed = 0
        AND mode = ?
    """
    cur.execute(sql, [mode])
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


def task_update(conn: Connection, task_id: int, task_text: str, url: Optional[str] = None):
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
    """Migrate database schema to add mode column and url column."""
    cur = conn.cursor()

    current_version = get_schema_version(conn)

    if current_version < 1:
        # This handles databases created before the schema_version table existed
        # and before the 'mode' column was introduced via the old migrate_schema.
        # Check if mode column exists
        cur.execute("PRAGMA table_info(tasks)")
        columns = cur.fetchall()
        has_mode = any(col[1] == 'mode' for col in columns)

        if not has_mode:
            # Add mode column with default value
            cur.execute("""
                ALTER TABLE tasks
                ADD COLUMN mode TEXT DEFAULT 'A'
                CHECK(mode IN ('A', 'B', 'C'))
            """)
            conn.commit() # Commit after adding mode

        # At this point, 'mode' column exists or was just added.
        # Now introduce schema_version table and set version to 1.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
            """
        )
        cur.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (1)")
        conn.commit() # Commit after setting version to 1
        current_version = 1 # Update current_version for subsequent migrations

    if current_version < 2:
        # Migration for adding the 'url' column
        cur.execute("PRAGMA table_info(tasks)")
        columns = cur.fetchall()
        has_url = any(col[1] == 'url' for col in columns)

        if not has_url:
            cur.execute("""
                ALTER TABLE tasks
                ADD COLUMN url TEXT
            """)
            conn.commit() # Commit after adding url

        # Update schema version to 2
        cur.execute("UPDATE schema_version SET version = 2")
        conn.commit()