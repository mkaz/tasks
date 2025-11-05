from sqlite3 import Connection, Error
from typing import List, Optional

from tasks.task import Task


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()

    # Create projects table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
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
            notes TEXT,
            priority INTEGER DEFAULT 2,
            state TEXT DEFAULT 'Backlog',
            project_id INTEGER DEFAULT 1,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        """
    )

    # Create default project if no projects exist
    cur.execute("SELECT COUNT(*) FROM projects")
    if cur.fetchone()[0] == 0:
        cur.execute(
            """
            INSERT INTO projects (id, title, is_active)
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


def get_tasks(conn: Connection, project_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()
    if project_id is not None:
        cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 AND project_id = ? ORDER BY priority, id", [project_id])
    else:
        # Get active project if no project_id specified
        active_project = get_active_project(conn)
        if active_project:
            cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 AND project_id = ? ORDER BY priority, id", [active_project['id']])
        else:
            cur.execute("SELECT * FROM tasks WHERE dt_completed = 0 ORDER BY priority, id")
    rows = cur.fetchall()
    return [Task(**dict(row)) for row in rows]


def get_tasks_new(conn: Connection, days: int, project_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()

    if project_id is not None:
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed = 0
               AND project_id = ?
               AND dt_created >= date('now', '-{days} days')
             ORDER BY priority, id
        """
        cur.execute(sql, [project_id])
    else:
        # Get active project if no project_id specified
        active_project = get_active_project(conn)
        if active_project:
            sql = f"""
                SELECT * FROM tasks
                 WHERE dt_completed = 0
                   AND project_id = ?
                   AND dt_created >= date('now', '-{days} days')
                 ORDER BY priority, id
            """
            cur.execute(sql, [active_project['id']])
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


def get_tasks_com(conn: Connection, days: int, project_id: Optional[int] = None) -> List[Task]:
    cur = conn.cursor()
    
    if project_id is not None:
        sql = f"""
            SELECT * FROM tasks
             WHERE dt_completed >= date('now', '-{days} days')
               AND project_id = ?
        """
        cur.execute(sql, [project_id])
    else:
        # Get active board if no project_id specified
        active_project = get_active_project(conn)
        if active_project:
            sql = f"""
                SELECT * FROM tasks
                 WHERE dt_completed >= date('now', '-{days} days')
                   AND project_id = ?
            """
            cur.execute(sql, [active_project['id']])
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
    """Set task state to one of: Now, Backlog, Done, Archive"""
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


def get_tasks_by_state(conn: Connection, state: str, project_id: Optional[int] = None) -> List[Task]:
    """Get all tasks for a specific state"""
    cur = conn.cursor()
    
    if project_id is not None:
        sql = """
            SELECT * FROM tasks
            WHERE dt_completed = 0
                AND state = ?
                AND project_id = ?
            ORDER BY priority, id
        """
        cur.execute(sql, [state, project_id])
    else:
        # Get active board if no project_id specified
        active_project = get_active_project(conn)
        if active_project:
            sql = """
                SELECT * FROM tasks
                WHERE dt_completed = 0
                    AND state = ?
                    AND project_id = ?
                ORDER BY priority, id
            """
            cur.execute(sql, [state, active_project['id']])
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

    # Check if projects table exists, or if boards table needs renaming
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
    has_projects_table = cur.fetchone() is not None

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='boards'")
    has_boards_table = cur.fetchone() is not None

    # Migrate boards table to projects table if needed
    if has_boards_table and not has_projects_table:
        print("Migrating boards table to projects table...")
        cur.execute("ALTER TABLE boards RENAME TO projects")
        conn.commit()
        print("Successfully renamed boards table to projects.")

    # Create projects table if it doesn't exist
    if not has_projects_table and not has_boards_table:
        print("Creating projects table...")
        cur.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create default project
        cur.execute("""
            INSERT INTO projects (id, title, is_active)
            VALUES (1, 'General', 1)
        """)
        conn.commit()
        print("Created projects table with default 'General' project.")

    # Get current columns in tasks table
    cur.execute("PRAGMA table_info(tasks)")
    columns = cur.fetchall()

    has_state = any(col[1] == "state" for col in columns)
    has_mode = any(col[1] == "mode" for col in columns)
    has_project_id = any(col[1] == "project_id" for col in columns)
    has_board_id = any(col[1] == "board_id" for col in columns)

    # Handle mode -> state migration and add project_id
    if has_mode and not has_state:
        print("Migrating schema: renaming mode to state and adding project_id...")
        # SQLite doesn't support renaming columns directly, so we need to recreate the table
        cur.execute("ALTER TABLE tasks RENAME TO tasks_old")
        
        # Create new table with 'state', 'project_id', and 'notes' columns
        cur.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                url TEXT,
                notes TEXT,
                priority INTEGER DEFAULT 2,
                state TEXT DEFAULT 'Backlog',
                project_id INTEGER DEFAULT 1,
                dt_completed DATETIME DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)
        
        # Copy data from old table, renaming mode to state and adding project_id
        cur.execute("""
            INSERT INTO tasks (id, task, url, priority, state, project_id, dt_completed, dt_created)
            SELECT id, task, url, priority, mode, 1, dt_completed, dt_created
            FROM tasks_old
        """)
        
        # Drop old table
        cur.execute("DROP TABLE tasks_old")
        conn.commit()
        print("Successfully migrated schema with state and project_id columns.")
    
    # Add state column if neither exists (for very old schemas)
    elif not has_state and not has_mode:
        print("Adding state column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN state TEXT DEFAULT 'Backlog'
        """)
        conn.commit()

    # Migrate board_id to project_id if needed
    if has_board_id and not has_project_id:
        print("Migrating board_id column to project_id...")
        # SQLite doesn't support renaming columns directly, so we need to recreate the table
        cur.execute("ALTER TABLE tasks RENAME TO tasks_old")

        # Get all column info to preserve them
        cur.execute("PRAGMA table_info(tasks_old)")
        old_columns = cur.fetchall()
        has_notes_in_old = any(col[1] == "notes" for col in old_columns)
        has_url_in_old = any(col[1] == "url" for col in old_columns)

        # Build column list for the new table
        cur.execute("""
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY,
                task TEXT NOT NULL,
                url TEXT,
                notes TEXT,
                priority INTEGER DEFAULT 2,
                state TEXT DEFAULT 'Backlog',
                project_id INTEGER DEFAULT 1,
                dt_completed DATETIME DEFAULT 0,
                dt_created DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        """)

        # Copy data, renaming board_id to project_id
        # Build dynamic SELECT based on available columns
        if has_notes_in_old and has_url_in_old:
            cur.execute("""
                INSERT INTO tasks (id, task, url, notes, priority, state, project_id, dt_completed, dt_created)
                SELECT id, task, url, notes, priority, state, board_id, dt_completed, dt_created
                FROM tasks_old
            """)
        elif has_url_in_old:
            cur.execute("""
                INSERT INTO tasks (id, task, url, priority, state, project_id, dt_completed, dt_created)
                SELECT id, task, url, priority, state, board_id, dt_completed, dt_created
                FROM tasks_old
            """)
        else:
            cur.execute("""
                INSERT INTO tasks (id, task, priority, state, project_id, dt_completed, dt_created)
                SELECT id, task, priority, state, board_id, dt_completed, dt_created
                FROM tasks_old
            """)

        cur.execute("DROP TABLE tasks_old")
        conn.commit()
        print("Successfully migrated board_id to project_id.")
    # Add project_id column if missing (and board_id doesn't exist)
    elif not has_project_id and not has_board_id:
        print("Adding project_id column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN project_id INTEGER DEFAULT 1
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

    # Add notes column if missing
    has_notes = any(col[1] == "notes" for col in columns)
    if not has_notes:
        print("Adding notes column...")
        cur.execute("""
            ALTER TABLE tasks
                ADD COLUMN notes TEXT
        """)
        conn.commit()

    # Migrate existing "Now" tasks to "Backlog" (two-section workflow)
    cur.execute("SELECT COUNT(*) FROM tasks WHERE state = 'Now'")
    now_count = cur.fetchone()[0]
    if now_count > 0:
        print(f"Migrating {now_count} tasks from 'Now' to 'Backlog'...")
        cur.execute("UPDATE tasks SET state = 'Backlog' WHERE state = 'Now'")
        conn.commit()
        print("Successfully migrated 'Now' tasks to 'Backlog'.")


def create_project(conn: Connection, title: str) -> Optional[int]:
    """Create a new project and return its ID."""
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO projects (title) VALUES (?)", [title])
        conn.commit()
        return cur.lastrowid
    except Exception:
        conn.rollback()
        return None


def get_projects(conn: Connection) -> List[dict]:
    """Get all projects."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY dt_created")
    rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_active_project(conn: Connection) -> Optional[dict]:
    """Get the currently active project."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE is_active = 1 LIMIT 1")
    row = cur.fetchone()
    if row:
        return dict(row)

    # If no active project, make the first project active
    cur.execute("SELECT * FROM projects ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if row:
        project_id = row[0]
        set_active_project(conn, project_id)
        return dict(row)

    return None


def set_active_project(conn: Connection, project_id: int) -> bool:
    """Set the active project."""
    cur = conn.cursor()
    try:
        # First, deactivate all projects
        cur.execute("UPDATE projects SET is_active = 0")
        # Then activate the specified project
        cur.execute("UPDATE projects SET is_active = 1 WHERE id = ?", [project_id])
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False


def delete_project(conn: Connection, project_id: int) -> bool:
    """Delete a project and move its tasks to the default project (id=1)."""
    cur = conn.cursor()
    try:
        # Don't allow deleting the default project
        if project_id == 1:
            return False

        # Move all tasks from this project to the default project
        cur.execute("UPDATE tasks SET project_id = 1 WHERE project_id = ?", [project_id])

        # Delete the project
        cur.execute("DELETE FROM projects WHERE id = ?", [project_id])

        # If this was the active project, make default project active
        cur.execute("SELECT COUNT(*) FROM projects WHERE is_active = 1")
        if cur.fetchone()[0] == 0:
            cur.execute("UPDATE projects SET is_active = 1 WHERE id = 1")

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
