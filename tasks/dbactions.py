from sqlite3 import Connection, Error
from typing import List, Optional

from tasks.task import Task


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()

    # Create boards table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Create tasks table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            url TEXT,
            priority INTEGER DEFAULT 2,
            state TEXT DEFAULT 'Now',
            board_id INTEGER DEFAULT 1,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES boards (id)
        )
        """
    )

    # Create default board if no boards exist
    cur.execute("SELECT COUNT(*) FROM boards")
    if cur.fetchone()[0] == 0:
        cur.execute(
            """
            INSERT INTO boards (id, title, is_active)
            VALUES (1, 'General', 1)
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


def get_tasks(conn: Connection, board_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()
    if board_id is not None:
        cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 AND board_id = ? ORDER BY priority, id", [board_id])
    else:
        # Get active board if no board_id specified
        active_board = get_active_board(conn)
        if active_board:
            cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 AND board_id = ? ORDER BY priority, id", [active_board['id']])
        else:
            cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 ORDER BY priority, id")
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def get_tasks_new(conn: Connection, days: int, board_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()
    
    if board_id is not None:
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed = 0
               AND board_id = ?
               AND dt_created >= date('now', '-{days} days')
             ORDER BY priority, id
        """
        cur.execute(sql, [board_id])
    else:
        # Get active board if no board_id specified
        active_board = get_active_board(conn)
        if active_board:
            sql = f"""
                SELECT * FROM tasks
                 WHERE dt_completed = 0
                   AND board_id = ?
                   AND dt_created >= date('now', '-{days} days')
                 ORDER BY priority, id
            """
            cur.execute(sql, [active_board['id']])
        else:
            sql = f"""
                SELECT * FROM tasks
                 WHERE dt_completed = 0
                   AND dt_created >= date('now', '-{days} days')
                 ORDER BY priority, id
            """
            cur.execute(sql)
    
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def get_tasks_com(conn: Connection, days: int, board_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()
    
    if board_id is not None:
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed >= date('now', '-{days} days')
               AND board_id = ?
        """
        cur.execute(sql, [board_id])
    else:
        # Get active board if no board_id specified
        active_board = get_active_board(conn)
        if active_board:
            sql = f"""
                SELECT * FROM tasks
                 WHERE dt_completed >= date('now', '-{days} days')
                   AND board_id = ?
            """
            cur.execute(sql, [active_board['id']])
        else:
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


def get_tasks_by_state(conn: Connection, state: str, board_id: Optional[int] = None) -> List[Task]:
    """Get all tasks for a specific state"""
    cur = conn.cursor()
    
    if board_id is not None:
        sql = """
            SELECT * FROM tasks
            WHERE dt_completed = 0
                AND state = ?
                AND board_id = ?
            ORDER BY priority, id
        """
        cur.execute(sql, [state, board_id])
    else:
        # Get active board if no board_id specified
        active_board = get_active_board(conn)
        if active_board:
            sql = """
                SELECT * FROM tasks
                WHERE dt_completed = 0
                    AND state = ?
                    AND board_id = ?
                ORDER BY priority, id
            """
            cur.execute(sql, [state, active_board['id']])
        else:
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

    # Check if boards table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boards'")
    has_boards_table = cur.fetchone() is not None

    # Create boards table if it doesn't exist
    if not has_boards_table:
        print("Creating boards table...")
        cur.execute("""
            CREATE TABLE boards (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default board
        cur.execute("""
            INSERT INTO boards (id, title, is_active)
            VALUES (1, 'General', 1)
        """)
        conn.commit()
        print("Created boards table with default 'General' board.")

    # Get current columns in tasks table
    cur.execute("PRAGMA table_info(tasks)")
    columns = cur.fetchall()

    has_state = any(col[1] == "state" for col in columns)
    has_mode = any(col[1] == "mode" for col in columns)
    has_board_id = any(col[1] == "board_id" for col in columns)

    # Handle mode -> state migration and add board_id
    if has_mode and not has_state:
        print("Migrating schema: renaming mode to state and adding board_id...")
        # SQLite doesn't support renaming columns directly, so we need to recreate the table
        cur.execute("ALTER TABLE tasks RENAME TO tasks_old")
        
        # Create new table with 'state' and 'board_id' columns
        cur.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                url TEXT,
                priority INTEGER DEFAULT 2,
                state TEXT DEFAULT 'Now',
                board_id INTEGER DEFAULT 1,
                dt_completed DATETIME DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES boards (id)
            )
        """)
        
        # Copy data from old table, renaming mode to state and adding board_id
        cur.execute("""
            INSERT INTO tasks (id, task, url, priority, state, board_id, dt_completed, dt_created)
            SELECT id, task, url, priority, mode, 1, dt_completed, dt_created
            FROM tasks_old
        """)
        
        # Drop old table
        cur.execute("DROP TABLE tasks_old")
        conn.commit()
        print("Successfully migrated schema with state and board_id columns.")
    
    # Add state column if neither exists (for very old schemas)
    elif not has_state and not has_mode:
        print("Adding state column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN state TEXT DEFAULT 'Now'
        """)
        conn.commit()

    # Add board_id column if missing
    if not has_board_id:
        print("Adding board_id column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN board_id INTEGER DEFAULT 1
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


def create_board(conn: Connection, title: str) -> Optional[int]:
    """Create a new board and return its ID."""
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO boards (title) VALUES (?)", [title])
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        return None


def get_boards(conn: Connection) -> List[dict]:
    """Get all boards."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM boards ORDER BY dt_created")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_active_board(conn: Connection) -> Optional[dict]:
    """Get the currently active board."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM boards WHERE is_active = 1 LIMIT 1")
    row = cur.fetchone()
    if row:
        return dict(row)
    
    # If no active board, make the first board active
    cur.execute("SELECT * FROM boards ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if row:
        board_id = row[0]
        set_active_board(conn, board_id)
        return dict(row)
    
    return None


def set_active_board(conn: Connection, board_id: int) -> bool:
    """Set the active board."""
    cur = conn.cursor()
    try:
        # First, deactivate all boards
        cur.execute("UPDATE boards SET is_active = 0")
        # Then activate the specified board
        cur.execute("UPDATE boards SET is_active = 1 WHERE id = ?", [board_id])
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False


def delete_board(conn: Connection, board_id: int) -> bool:
    """Delete a board and move its tasks to the default board (id=1)."""
    cur = conn.cursor()
    try:
        # Don't allow deleting the default board
        if board_id == 1:
            return False
            
        # Move all tasks from this board to the default board
        cur.execute("UPDATE tasks SET board_id = 1 WHERE board_id = ?", [board_id])
        
        # Delete the board
        cur.execute("DELETE FROM boards WHERE id = ?", [board_id])
        
        # If this was the active board, make default board active
        cur.execute("SELECT COUNT(*) FROM boards WHERE is_active = 1")
        if cur.fetchone()[0] == 0:
            cur.execute("UPDATE boards SET is_active = 1 WHERE id = 1")
        
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
