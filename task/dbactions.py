from sqlite3 import Connection
from typing import List


def create_schema(conn: Connection):
    """Create schema. Will not overwrite if exists"""
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            task TEXT NOT NULL,
            dt_completed DATETIME DEFAULT 0,
            dt_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def get_tasks(conn: Connection) -> List:
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE dt_completed = 0")
    return cur.fetchall()


def insert_task(conn: Connection, task: str) -> int:
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


def task_delete(conn: Connection, task_id: int):
    """Mark task id done"""
    cur = conn.cursor()
    sql = """
        DELETE FROM tasks 
         WHERE id = ?
    """
    cur.execute(sql, [task_id])
    conn.commit()
