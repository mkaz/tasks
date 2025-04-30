from sqlite3 import Connection
from typing import List, Optional


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER DEFAULT 2,
            mode TEXT DEFAULT 'A' CHECK(mode IN ('A', 'B', 'C'))
        )
        """
    )

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


def task_update(conn: Connection, task_id: int, task: str):
    """Update task with new text"""
    cur = conn.cursor()
    sql = """
        UPDATE tasks
           SET task = ?
         WHERE id = ?
    """
    cur.execute(sql, [task, task_id])
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
    """Migrate database schema to add mode column"""
    cur = conn.cursor()

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
        conn.commit()
