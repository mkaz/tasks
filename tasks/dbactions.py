from sqlite3 import Connection, Error
from typing import List, Optional

from tasks.task import Task


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            url TEXT,
            priority INTEGER DEFAULT 2,
            state TEXT DEFAULT 'Now',
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
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


def set_task_state(conn: Connection, task_id: int, state: str):
    """Set task state to one of: Now, Later, Done, Archive"""
    cur = conn.cursor()
    # LIMIT clause is not needed in UPDATE statement since WHERE id = ?
    # already ensures we only update one row (id is primary key)
    sql = """
        UPDATE tasks
           SET state = ?
         WHERE id = ?
    """
    cur.execute(sql, [state, task_id])
    conn.commit()


def get_tasks_by_state(conn: Connection, state: str) -> List[Task]:
    """Get all tasks for a specific state"""
    cur = conn.cursor()
    sql = """
        SELECT * FROM tasks
        WHERE dt_completed = 0
            AND state = ?
        ORDER BY priority, id
    """
    cur.execute(sql, [state])
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def migrate_schema(conn: Connection) -> None:
    """Migrate database schema."""

    cur = conn.cursor()

    # Drop schema_version table - not needed anymore
    cur.execute("DROP TABLE IF EXISTS schema_version")
    conn.commit()

    # Get current columns
    cur.execute("PRAGMA table_info(tasks)")
    columns = cur.fetchall()

    has_state = any(col[1] == "state" for col in columns)
    has_mode = any(col[1] == "mode" for col in columns)

    # If we have old 'mode' column but not 'state', rename it
    if has_mode and not has_state:
        print("Renaming mode column to state...")
        # SQLite doesn't support renaming columns directly, so we need to recreate the table
        cur.execute("ALTER TABLE tasks RENAME TO tasks_old")
        
        # Create new table with 'state' column
        cur.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                url TEXT,
                priority INTEGER DEFAULT 2,
                state TEXT DEFAULT 'Now',
                dt_completed DATETIME DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copy data from old table, renaming mode to state
        cur.execute("""
            INSERT INTO tasks (id, task, url, priority, state, dt_completed, dt_created)
            SELECT id, task, url, priority, mode, dt_completed, dt_created
            FROM tasks_old
        """)
        
        # Drop old table
        cur.execute("DROP TABLE tasks_old")
        conn.commit()
        print("Successfully renamed mode column to state.")
    
    # Add state column if neither exists (for very old schemas)
    elif not has_state and not has_mode:
        print("Adding state column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN state TEXT DEFAULT 'Now'
        """)
        conn.commit()

    # Add url column if missing
    has_url = any(col[1] == "url" for col in columns)
    if not has_url:
        print("Adding url column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN url TEXT
        """)
        conn.commit()
